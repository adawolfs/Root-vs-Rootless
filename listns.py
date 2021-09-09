#!/usr/bin/python

import os
import fnmatch
 
if os.geteuid() != 0:
    print("This script must be run as root\nBye")
    exit(1)
 
def getinode( pid , type):
    link = '/proc/' + pid + '/ns/' + type
    ret = ''
    try:
        ret = os.readlink( link )
    except OSError as e:
        ret = ''
        pass
    return ret
 
#
# get the running command
def getcmd( p ):
    try:
        cmd = open(os.path.join('/proc', p, 'cmdline'), 'rb').read()
        if cmd == '':
            cmd = open(os.path.join('/proc', p, 'comm'), 'rb').read()
        cmd = cmd.replace('\x00' , ' ')
        cmd = cmd.replace('\n' , ' ')
        return cmd
    except:
        return ''
#
# look for docker parents
def getpcmd( p ):
    try:
        f = '/proc/' + p + '/stat'
        arr = open( f, 'rb').read().split()
        cmd = getcmd( arr[3] )
        if cmd.startswith( '/usr/bin/docker' ):
            return 'docker'
    except:
        pass
    return ''
#
# get the namespaces of PID=1
# assumption: these are the namespaces supported by the system
#
nslist = os.listdir('/proc/1/ns/')
if len(nslist) == 0:
    print('No Namespaces found for PID=1')
    exit(1)
#print nslist
#
# get the inodes used for PID=1
#
baseinode = []
for x in nslist:
    baseinode.append( getinode( '1' , x ) )
#print "Default namespaces: " , baseinode
err = 0
ns = []
ipnlist = []
#
# loop over the network namespaces created using "ip"
#
try:
    netns = os.listdir('/var/run/netns/')
    for p in netns:
        fd = os.open( '/var/run/netns/' + p, os.O_RDONLY )
        info = os.fstat(fd)
        os.close( fd)
        ns.append( '-- net:[' + str(info.st_ino) + '] created by ip netns add ' + p )
        ipnlist.append( 'net:[' + str(info.st_ino) + ']' )
except:
    # might fail if no network namespaces are existing
    pass
#
# walk through all pids and list diffs
#
pidlist = fnmatch.filter(os.listdir('/proc/'), '[0123456789]*')
#print pidlist
for p in pidlist:
    try:
        pnslist = os.listdir('/proc/' + p + '/ns/')
        for x in pnslist:
            i = getinode ( p , x )
            if i != '' and i not in baseinode:
                cmd = getcmd( p )
                pcmd = getpcmd( p )
                if pcmd != '':
                    cmd = '[' + pcmd + '] ' + cmd
                tag = ''
                if i in ipnlist:
                    tag='**' 
                ns.append( p + ' ' + i + tag + ' ' + cmd)
    except:
        # might happen if a pid is destroyed during list processing
        pass
#
# print the stuff
#
print('{0:>10}  {1:20}  {2}'.format('PID','Namespace','Thread/Command'))
for e in ns:
    x = e.split( ' ' , 2 )
    print('{0:>10}  {1:20}  {2}'.format(x[0],x[1],x[2][:60]))
#