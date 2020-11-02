# -*- coding: utf-8 -*-
import os, sys
import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np
import pandas as pd

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
            i = limitsize-1
        min_val = limits[i]
        min_c = rop[i]
        if i == limitsize-1:
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


# slice the source image to smaller tiles, calculate the average grey value
def get_grey_values( image, row_count, col_count ):
    height, width = image.shape[:2]

    #cropping width / height
    crop_height = int(height/row_count)
    crop_width = int(width/col_count)

    grey_values = []

    for i in range(row_count): # start at i = 0 to row_count-1
        for j in range(col_count): # start at j = 0 to col_count-1
            image_slice = image[(i*crop_height):((i+1)*crop_height), (j*crop_width):((j+1)*crop_width)]#  image.crop( ((j*crop_width), (i*crop_height), ((j+1)*crop_width), ((i+1)*crop_height)) )
            grey_values.append( np.mean(image_slice) )

    return grey_values

if __name__ == '__main__':
    programInfo()

    limits = [2, 4, 8, 16, 32, 63, 125, 250, 500] #particle size limits

    # prepare pandas dataframe column names
    extended_limits = limits + [1000]
    pandas_columns = ['image']
    last_border = 0
    for limit in extended_limits:
        pandas_columns.append( '{}-{}'.format(last_border, limit) )
        last_border = limit
    pandas_columns += ['masked (px)', 'masked (%)', 'd95', 'grey 2x2 mean', 'grey 2x2 std', 'grey 5x3 mean', 'grey 5x3 std']

    result_df = pd.DataFrame(columns = pandas_columns)

    working_directory = filedialog.askdirectory(title='Please select the working directory')
    image_count = 0
    if os.path.isdir(working_directory):
        # create output folder
        output_directory = working_directory + '/cv/'
        if not os.path.exists(output_directory):
            os.mkdir(output_directory)

        # counting available CSV files
        for file in os.listdir(working_directory):
            if ( file.endswith( ".jpg" ) ):
                image_count += 1

        # processing CSV files
        result_list          = [] # list containing results of every single image
        experiment_tile_list = {} # dictionary containing results of a single specimen (set of 9 images)
        experiment_list      = {} # dictionary containing results of an 5 times repeated experiment (set of 5 x 9 images)
        pos = 0
        for file in os.listdir(working_directory):
            if ( file.endswith( ".jpg" ) ):
                pos += 1
                print('processing file {} ({:02d} of {:02d})'.format( file, pos, image_count ))
                # basic file handling
                # expecting a filename as follows: {experiment}_[a-e]_[1-9]
                # eg: 0-0_a_1.jpg, HG_c_8.jpg
                basename = os.path.splitext(os.path.basename(file))[0]

                # open image
                image = cv2.imread(working_directory + os.sep + file)
                height, width = image.shape[:2]

                # convert to grayscale
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                #cv2.imwrite( output_directory + basename + '_gs.jpg', image)

                # enhance histogram in a similar manner as in ImageJ
                image = stretchHistogram(image, saturated=0.35)
                #cv2.imwrite(output_directory + basename + '_eq.jpg', image)

                # set a threshold of 130 and binarise the image
                _, im_th = cv2.threshold(image, 130, 255, cv2.THRESH_BINARY)
                im_th_inv = cv2.bitwise_not(im_th)
                #cv2.imwrite( output_directory + basename + '_th.png', im_th_inv)

                # get the particles and their respective area
                contours, hierarchy = cv2.findContours(im_th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                areas = []
                contourCount = len(contours)
                for i in range(0, contourCount):
                    if cv2.contourArea(contours[i]) > 0:
                        areas.append(cv2.contourArea(contours[i]))
                #print(len(areas))
                #print('-'*10)

                # write to a dataframe and CSV
                particle_df = pd.DataFrame()

                particle_df = particle_df.append(areas, ignore_index=True)
                particle_df.to_csv(output_directory + basename + '_psd.csv', index=False)

                a   = [] # list of sums of the particle sizes within given limits
                b   = [] # list of sums of the particle sizes to the given limit
                rop = [] # list of the "rate of passage" to the given limit
                rop_output = ''
                area_sum = sum(areas)

                for i in range(len(limits)):
                    b.append(0)

                    if i == 0: lowerlimit = 0
                    else: lowerlimit = limits[i-1]

                    if i == len(limits): upperlimit = "max"
                    else: upperlimit = limits[i]

                    a.append( getarea(areas, lowerlimit, upperlimit) )
                    for j in range(i+1):
                        b[i] += a[j]

                    rop.append( 100 / area_sum * b[i] )
                    rop_output += str(round(rop[i],2)) + ", "

                maxsize = np.amax(area_sum)
                masked = round((100/(height*width)*area_sum), 2)
                d95 = getDx(95, rop, maxsize, limits)

                # grayscale analysis
                grey_5_3 = get_grey_values( im_th, row_count=3, col_count=5 )
                grey_2_2 = get_grey_values( im_th, row_count=2, col_count=2 )

                # generate table of the results of every image
                result_row = [basename] + rop + [100, maxsize, masked, d95, np.mean(grey_2_2), np.std(grey_2_2), np.mean(grey_5_3), np.std(grey_5_3)]
                result_list.append(result_row)
                result_df = result_df.append(pd.Series(result_row, index=pandas_columns), ignore_index=True)

        #result_df = result_df.append(pd.Series(result_list, index=pandas_columns), ignore_index=True)
        print(result_df)
        result_df.to_csv(output_directory + 'result.csv', index=False)
        #experiment_tile_columns = {'d95'=0, 'grey 2x2 mean'=0, 'grey 5x3 mean'=0}
        #for index, row in result_df.iterrows:
        #    basename_split = row['image'].split("_")
        #    experiment_tile_list[basename_split[0] + '_' + basename_split[1]] += item['']

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