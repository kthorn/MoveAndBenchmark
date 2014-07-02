# -*- coding: utf-8 -*-
"""

Code for moving data from SSD to HD
On run:
   * Create new folder on destination HD named today's date
   * Traverse over source SSD and move files to new folder
   * Delete source files
   
   * Log number of GB deleted from SSD
   * Benchmark SSD write speed
    
Created on Sun Feb 16 14:30:28 2014

@author: kthorn
"""

import os, time, subprocess, shutil, re, ctypes, sys, stat

#Parameters
MOVE = False; #Do file moving?
BENCHMARK = False; #Do disk speed benchmarking?
source = 'D:\\Data\\' #source directory (SSD)
dest = 'D:\\Data\\' #destination directory (HD)
logfile = 'C:\\Admin\\log.txt'
deletedays = 30 #delete files on dest older than this many days
pathToParkdale = 'C:\\Admin\\ParkdaleCmd'

#Probably don't need to change these
MMre = 'javaw.exe.+Console' #regexp to find MM in tasklist
Elements_re = 'nis_ar' #regexp to find NIS-Elements in tasklist
Nspeed_measurements = 5 #How many times to repeat drive speed measurement

sourceDrive = re.search('(\w:)', source).group(1) #Source drive letter
destDrive = re.search('(\w:)', dest).group(1) #Destination drive letter

def has_hidden_attribute(filepath):
    try:
        attrs = ctypes.windll.kernel32.GetFileAttributesW(unicode(filepath))
        assert attrs != -1
        result = bool(attrs & 2)
    except (AttributeError, AssertionError):
        result = False
    return result

def acquisition_running():    
    processes = subprocess.check_output('tasklist')
    if re.search(MMre, processes) or re.search(Elements_re, processes):
        return True
    else:
        return False
    
#open logfile
log = open(logfile,'a')
#get current date
today = time.strftime("%Y%m%d_%H%M%S")
 
#quit if Micro-manager is running
if acquisition_running():
    log.write(today + ' Acquisition software running, terminating file move\r\n')
    log.close()
    sys.exit(1)

#first, delete files older than X days on dest
now = time.time();
deletesecs = deletedays*24*60*60;

for root, dirs, files in os.walk(dest, topdown=False):
    for name in files:
        filepath = (os.path.join(root, name));
        #print(filepath + ' ' + now - str(os.path.getmtime(filepath)) + '/r/n')
        if not has_hidden_attribute(filepath) and (now - os.path.getmtime(filepath)) > deletesecs:
            #print(filepath + ' ' + str(now - os.path.getmtime(filepath)) + '\r\n')
            try:
                os.remove(filepath)
            except WindowsError:
                #make file writable and try again
                os.chmod(filepath, stat.S_IWRITE)
                os.remove(filepath)
    for name in dirs:
        try:
            os.rmdir(os.path.join(root, name)) #os.rmdir won't delete non-empty dirs
        except OSError as ex:
            pass

#quit if Micro-manager is running; check again in case it has been started
if acquisition_running():
    log.write(today + ' Acquisition software running, terminating file move\r\n')
    log.close()
    sys.exit(1)

#get used disk space on source
wmic_out = subprocess.check_output(['wmic', 'logicaldisk', 'get', 'size,freespace,caption'])
m = re.search(sourceDrive+'\s+(\d+)\s+(\d+)', wmic_out) 
usedSpaceGBSource = (int(m.group(2))-int(m.group(1)))/1e9

if BENCHMARK:
    #check write speed - http://thesz.diecru.eu/content/parkdale.php
    #repeat and average for more accurate result
    speedSum = 0
    for i in range(Nspeed_measurements):
        speed_out = subprocess.check_output([pathToParkdale, '-d', sourceDrive, '-s', '1000'])
        m = re.search('write: (\d+)', speed_out)
        speedSum = speedSum + float(m.group(1))
    writeSpeed = speedSum / Nspeed_measurements;
    #log disk usage


if MOVE:
    #Move files from source to dest
    #First, check for sufficient space on destination drive
    wmic_out = subprocess.check_output(['wmic', 'logicaldisk', 'get', 'size,freespace,caption'])
    m = re.search(destDrive+'\s+(\d+)\s+(\d+)', wmic_out) 
    freeSpaceGBDest = int(m.group(1))/1e9
    if freeSpaceGBDest < usedSpaceGBSource:
        #abort move
        log.write(today + ' Not enough free space on destination; terminating file move\r\n')
        MOVE = False
    else:
        destdir = os.path.join(dest, today)
        #walk over files in source, making them writeable, so that we can delete them later
        for root, dirs, files in os.walk(source):
            for name in files:
                os.chmod(os.path.join(root, name), stat.S_IWRITE) #make writeable
        #get directory of source    
        list = os.listdir(source)
        #loop over files and directories, moving them
        for item in list:
            sourcestr = os.path.join(source, item)
            if not has_hidden_attribute(sourcestr):
                deststr = os.path.join(destdir, item)
                shutil.move(sourcestr, deststr)
        wmic_out = subprocess.check_output(['wmic', 'logicaldisk', 'get', 'size,freespace,caption'])
        m = re.search(sourceDrive+'\s+(\d+)\s+(\d+)', wmic_out) 
        movedGB = usedSpaceGBSource - (int(m.group(2))-int(m.group(1)))/1e9

#log results
if BENCHMARK or MOVE:                
    log.write(today+' ')
    if BENCHMARK:
        log.write('Moved: ' + str(movedGB) + ' ')
    if MOVE:
        log.write('WriteSpeed: ' + str(writeSpeed) + '\r\n')
    else:
        log.write('\r\n')
log.close()