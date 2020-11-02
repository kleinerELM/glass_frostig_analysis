# -*- coding: utf-8 -*-
import os, sys, getopt
import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np

#remove root windows
root = tk.Tk()
root.withdraw()

def programInfo():
    print("##########################################################")
    print("# Particle Size Analysis Script                          #")
    print("# written for ImageJ and PHP 5.6 by Florian Kleiner 2013 #")
    print("# translated to Python 3 by Florian Kleiner 2020         #")
    print("#                                                        #")
    print("# © 2020 Florian Kleiner                                 #")
    print("#   Bauhaus-Universität Weimar                           #")
    print("#   Finger-Institut für Baustoffkunde                    #")
    print("#                                                        #")
    print("##########################################################")
    print()

#sums areas
def getarea(lines, lowerlimit, upperlimit):
    result = 0
    for line in lines:
        if upperlimit != "max":
            if line > lowerlimit and line <= upperlimit:
                result += line
        elif line > lowerlimit:
            result += line

    return result

#function to get the Dx-value, eg. D95
def getDx(x, rop, maxsize, limits):
    limitsize = len(limits)
    min_val = 0
    min_c = 0
    result = ">500"
    for i in range(limitsize):
        if rop[i] > x:
            result = round((limits[i]-min_val) / (rop[i] - min_c) * (x - min_c) + min_val)
            i = limitsize        
        min_val = limits[i]
        min_c = rop[i]
        if i == limitsize:
            break

    if result == ">500":
        return round((maxsize - min_val) / (100 - min_c) * (x - min_c) + min_val)
    else:
        return result

# function as in ImageJ
# source: https://github.com/imagej/ImageJA/blob/master/src/main/java/ij/plugin/ContrastEnhancer.java
# int[] getMinAndMax(ImageProcessor ip, double saturated, ImageStatistics stats) { ... }
def getMinAndMax(image, histogram, bins, saturated=0.35):
    height, width = image.shape[:2]
    hsize = len(histogram)

    if saturated > 0:
        #actually I do not understand the 200 here, but the returned values fit well
        threshold = height*width*saturated/200
    else:
        threshold = 0
    
    count = 0
    for i in range(hsize):
        count += histogram[i]
        if count > threshold: break
    hmin = i

    count = 0
    for i in range(hsize-1, 0, -1):
        count += histogram[i]
        if count > threshold: break
    hmax = i

    return hmin, hmax

## enhance contrast function close to the functionality in imageJ
# source: https://github.com/imagej/ImageJA/blob/master/src/main/java/ij/plugin/ContrastEnhancer.java
# public void stretchHistogram(ImageProcessor ip, double saturated, ImageStatistics stats) { ... }
def stretchHistogram(image, saturated=0.35):
    bincount = 256 # 8-bit greyscale image
    hist, bins  = np.histogram(image.flatten(), bincount, [0,bincount])
    hmin, hmax = getMinAndMax(image, hist, bins, saturated)
    if hmax > hmin:
        # difference in imageJ: 
        # double min = stats.histMin+hmin*stats.binSize;
        # double max = stats.histMin+hmax*stats.binSize;
        # [...]
        # ip.setMinAndMax(min, max);
        table = np.interp(np.arange(bincount), [hmin, hmax], [0,bincount-1]).astype('uint8')
        image = table[image]
    else:
        print('Fatal error while stretching histogram!')
    return image

if __name__ == '__main__':
    programInfo()
    working_directory = filedialog.askdirectory(title='Please select the working directory')
    image_count = 0
    if os.path.isdir(working_directory):
        # counting available CSV files
        for file in os.listdir(working_directory):
            if ( file.endswith( ".jpg" ) ):
                image_count += 1
        
        # processing CSV files
        pos = 0
        for file in os.listdir(working_directory):
            if ( file.endswith( ".jpg" ) ):
                pos += 1
                print('processing file {} ({:02d} of {:02d})'.format( file, pos, image_count ))
                # open image
                image = cv2.imread(working_directory + os.sep + file)
                #convert to grayscale
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                cv2.imwrite( working_directory + '/cv/' + os.path.splitext(os.path.basename(file))[0] + '_gs.jpg', image)
                image = stretchHistogram(image)

                cv2.imwrite( working_directory + '/cv/' + os.path.splitext(os.path.basename(file))[0] + '_eq.jpg', image)

                _, im_th = cv2.threshold(image, 130, 255, cv2.THRESH_BINARY)
                
                im_th_inv = cv2.bitwise_not(im_th)
                cv2.imwrite( working_directory + '/cv/' + os.path.splitext(os.path.basename(file))[0] + '_th.png', im_th_inv)
                
                contours, hierarchy = cv2.findContours(im_th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
                areas = []
                contourCount = len(contours)
                for i in range(0, contourCount):
                    if cv2.contourArea(contours[i]) > 0:
                        areas.append(cv2.contourArea(contours[i]))
                print(len(areas))
                print('-'*10)
                #height, width = image.shape[:2]

                """
                fWrite($handler , $type[0].", ");

                #particle size analysis
                lines = []]
                $fp = @fopen($dir.$file, "r") or die (" Cant read file!");
                while ($line = fgets($fp, 1024)) {
                    $lines[] = intval($line);
                }
                fclose($fp);

                $max = getarea($lines, 0, "max");

                for ($i = 0; $i <= $limitsize; $i++) {
                    $b[$i] = 0;
                    if ($i == 0) {$lowerlimit = 0;}
                    else {$lowerlimit = $limits[$i-1];}
                    if ($i == $limitsize) {$upperlimit = "max";}
                    else {$upperlimit = $limits[$i];}

                    $a[$i] = getarea($lines, $lowerlimit, $upperlimit);
                    for ($j = 0; $j <= $i; $j++) {
                        $b[$i] += $a[$j];
                    }
                    $rop[$i] = 100/$max*$b[$i];
                    $ropoutoput += round($c[$i],2).", ";
                }

                $maxsize = max($lines);
                $masked = round((100/3211520*$max), 2); 
                $d95 = getDx(95, $rop, $maxsize);

                //grayscale analysis
                $grey = array();
                $fp = @fopen($dir."gs".$type[0].".txt", "r") or die (" Cant read file!");
                while ($line = fgets($fp, 1024)) {
                    $grey[] = intval($line);
                }
                fclose($fp);
                $sigma = getStDev($grey);

                //fileoutput
                """

"""
<?php
// Particle Size Analysis Script
// written by Florian Kleiner 2013
//
// important variables:
// $a[]		array of sums of the particle sizes within given limits
// $b[]		array of sums of the particle sizes to the given limit
// $d95		D95 value
// $grey[]	array of measured grey values
// $limits[]	array of particle size limits
// $limitsize	count of particle size limits
// $lines[]	array of measured particle sizes
// $lowerlimit	lower limit of particle sizes
// $masked	masked area of the picture in percent
// $max		masked area in pixel
// $maxsize	size of the largest particle
// $rop[]	array of the "rate of passage" to the given limit
// $sigma[]	array,  contains standard deviation an mean value of the grey values
// $upperlimit	upper limit of particle sizes
//
// all unmentioned variables are auxilary varibles
//
// call: PSA.php?dir=ORDNER
// outputfile is a csv which must be further evaluated



//function to get the Dx-value, eg. D95

//calculates standard deviation and mean 
function getStDev($data)
{
    $sum = $vsum = 0;
    foreach ($data as $value) {
        $sum += $value;
    }
    $mean = $sum / count($data);
    foreach($data as $value) {
       $tmp = $value - $mean;
       $tmp *= $tmp;
       $vsum += $tmp;
    }
    $stdev = sqrt( $vsum / (count($data)-1) );
    return array('mean' => $mean, 'stdev' => $stdev);
}

$dirname = $_GET['dir']; 

$dir = "./".$dirname."/";
$limits = array(2,4,8,16,32,63,125,250,500); //Korngrenzen
$limitsize = count($limits);

$handler = fopen( $dirname.".csv", "a+");

$dirhandler = openDir($dir);
while ($file = readDir($dirhandler)) {
    $type = explode(".",$file);
    if ($file != "." && $file != ".." && $type[count($type)-1]=="csv") {
        fWrite($handler , $type[0].", ");

        //particle size analysis
        $lines = array();
        $fp = @fopen($dir.$file, "r") or die (" Cant read file!");
        while ($line = fgets($fp, 1024)) {
            $lines[] = intval($line);
        }
        fclose($fp);

        $max = getarea($lines, 0, "max");

        for ($i = 0; $i <= $limitsize; $i++) {
            $b[$i] = 0;
            if ($i == 0) {$lowerlimit = 0;}
              else {$lowerlimit = $limits[$i-1];}
            if ($i == $limitsize) {$upperlimit = "max";}
              else {$upperlimit = $limits[$i];}

            $a[$i] = getarea($lines, $lowerlimit, $upperlimit);
            for ($j = 0; $j <= $i; $j++) {
                $b[$i] += $a[$j];
            }
            $rop[$i] = 100/$max*$b[$i];
            $ropoutoput += round($c[$i],2).", ";
        }

        $maxsize = max($lines);
        $masked = round((100/3211520*$max), 2); 
        $d95 = getDx(95, $rop, $maxsize);

        //grayscale analysis
        $grey = array();
        $fp = @fopen($dir."gs".$type[0].".txt", "r") or die (" Cant read file!");
        while ($line = fgets($fp, 1024)) {
            $grey[] = intval($line);
        }
        fclose($fp);
        $sigma = getStDev($grey);

        //fileoutput
        fWrite($handler , $ropoutoput.$maxsize.", ".$masked.", ".$d95.", ".round($sigma['mean'],1).", ".round($sigma['stdev'],2)."\n");
    }
}
closeDir($dirhandler);
fClose($handler)
?>
"""