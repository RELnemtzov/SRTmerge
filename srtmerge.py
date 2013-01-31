#SRTmerge Copyright 2013 (c) Ariel Nemtzov
#pysrt Copyright (c) Jean Boussier


#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.


#!/usr/bin/env python
import argparse
from pysrt import SubRipFile
import sys
import subprocess
import re
from decimal import Decimal
from pysrt.srttime import SubRipTime
import codecs
import os.path
 
def get_video_length(path):
    try:
        process = subprocess.Popen(['avconv', '-i', path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = process.communicate()
        matches = re.search(r"Duration:\s{1}(?P<hours>\d+?):(?P<minutes>\d+?):(?P<seconds>\d+\.\d+?),", stdout, re.DOTALL).groupdict()
     
        seconds = Decimal(matches['seconds']).quantize(Decimal('1.000'))
        secsAndMilli = str(seconds).partition('.')
        time = matches['hours'].zfill(2)+':'+matches['minutes'].zfill(2)+':'+secsAndMilli[0].zfill(2)+','+secsAndMilli[2].zfill(3)
        return SubRipTime.from_string(time)
    except AttributeError:
        print "No such file: ",path
        sys.exit(1)
    
    
if __name__ == '__main__' :
    parser = argparse.ArgumentParser()
    parser.add_argument('input1',
        help='The first srt file containing the first half of the original subs')
    parser.add_argument('input2',
        help='The second srt file containing the second half of the original subs')
    parser.add_argument('output',
        help='The file where the fixed subs should be saved')
    parser.add_argument('-i', '--inputVideo1', nargs=1,
        help='The first video file of the two to combine.')
    parser.add_argument('-o', '--offset2', nargs=1,
        help='Offset of second input file from end of first in format HH:MM:SS,mmm')
    parser.add_argument('-e', '--encoding', nargs=1,
        help='Encoding of the subtitle files, must be the same. Default is utf-8.')
    args = parser.parse_args()
    if not args.inputVideo1 and not args.offset2:
        parser.error('One of -i/--inputVideo1 or -o/--offset2 are required')
        sys.exit(1)
    zeroTime = "00:00:00,000"
    if args.inputVideo1:
        length1Time = get_video_length(args.inputVideo1[0])
        offset2Time = SubRipTime.from_string(zeroTime)
        inVid1 = args.inputVideo1[0]
    if args.offset2:
        offset2Time = SubRipTime.from_string(args.offset2[0])
        length1Time = SubRipTime.from_string(zeroTime)
        offset2 = args.offset2[0]
    inSubName1 = args.input1
    inSubName2 = args.input2
    outSubName = args.output
    if args.encoding:
        encoding = args.encoding[0]
    else:
        encoding = args.encoding
    try:
        inSub1 = SubRipFile.open(inSubName1,encoding)
    except AttributeError:
        print "No such file: ",inSubName1
        sys.exit(1)
    except LookupError:
        print "No such encoding: ",encoding
        sys.exit(1)
    except UnicodeDecodeError:
        print "Not encoded as utf-8"
        sys.exit(1)
    try:
        inSub2 = SubRipFile.open(inSubName2,encoding)
    except AttributeError:
        print "No such file: ",inSubName1
        sys.exit(1)
    except LookupError:
        print "No such encoding: ",encoding
        sys.exit(1)
    except UnicodeDecodeError:
        print "Not encoded as utf-8"
        sys.exit(1)
    if os.path.exists(outSubName):
        overwrite = 'n'
        prompt = "File "+outSubName+" already exists. Replace? [y,N] "
        sys.stdout.write(prompt)
        overwrite = sys.stdin.readline().rstrip("\n")
        if overwrite not in ('y','Y'):
            print "Aborted."
            sys.exit(1)
    try:
        outSub = codecs.open(outSubName,'w+',encoding)
    except LookupError:
        print "Encoding entered is incorrect: ",encoding
        sys.exit(1)
    except UnicodeDecodeError:
        print "Not encoded as utf-8"
        sys.exit(1)
    i=0
    curSub = inSub1[i]
    for SubRipFile in inSub1:
        curSub = inSub1[i]
        h1 = str('%02d' % curSub.start.hours)
        m1 = str('%02d' % curSub.start.minutes)
        s1 = str('%02d' % curSub.start.seconds)
        mm1 = str('%03d' % curSub.start.milliseconds)
        beginStr = h1+":"+m1+":"+s1+","+mm1
        h2 = str('%02d' % curSub.end.hours)
        m2 = str('%02d' % curSub.end.minutes)
        s2 = str('%02d' % curSub.end.seconds)
        mm2 = str('%03d' % curSub.end.milliseconds)
        endStr = h2+":"+m2+":"+s2+","+mm2
        tempSub = str(curSub.index)+"\n"+beginStr +" --> "+endStr+"\n"+curSub.text+"\n\n"
        outSub.write(tempSub)
        i+=1
    i=0
    lastSub1 = curSub
    for SubRipFile in inSub2:
        curSub = inSub2[i]
        curSub.shift(hours=length1Time.hours,minutes=length1Time.minutes,seconds=length1Time.seconds,milliseconds= length1Time.milliseconds)
        curSub.shift(hours=offset2Time.hours,minutes=offset2Time.minutes,seconds=offset2Time.seconds,milliseconds= offset2Time.milliseconds)
        curSub.index += lastSub1.index
        h1 = str('%02d' % curSub.start.hours)
        m1 = str('%02d' % curSub.start.minutes)
        s1 = str('%02d' % curSub.start.seconds)
        mm1 = str('%03d' % curSub.start.milliseconds)
        beginStr = h1+":"+m1+":"+s1+","+mm1
        h2 = str('%02d' % curSub.end.hours)
        m2 = str('%02d' % curSub.end.minutes)
        s2 = str('%02d' % curSub.end.seconds)
        mm2 = str('%03d' % curSub.end.milliseconds)
        endStr = h2+":"+m2+":"+s2+","+mm2
        tempSub = str(curSub.index)+"\n"+beginStr +" --> "+endStr+"\n"+curSub.text+"\n\n"
        outSub.write(tempSub)
        i+=1
    outSub.close()
    print "Done."