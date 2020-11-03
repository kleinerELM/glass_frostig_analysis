# -*- coding: utf-8 -*-
import os, sys, math
import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np
import pandas as pd
import subprocess
from subprocess import check_output
import multiprocessing

#remove root windows
root = tk.Tk()
root.withdraw()

def programInfo():
    print("##########################################################")
    print("# Particle Size Analysis Script                          #")
    print("# originally written for ImageJ and PHP 5.6              #")
    print("# by Florian Kleiner 2012/2013                           #")
    print("#                                                        #")
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

class glass_frosting_analysis():
    #particle size limits
    limits = [2, 4, 8, 16, 32, 63, 125, 250, 500]
    limitlen = len(limits)

    # prepare pandas dataframe column names
    extended_limits = limits + [1000]
    pandas_columns = ['image']
    last_border = 0
    for limit in extended_limits:
        pandas_columns.append( '{}-{}'.format(last_border, limit) )
        last_border = limit
    pandas_columns += ['masked (px)', 'masked (%)', 'd95', 'grey 2x2 mean', 'grey 2x2 std', 'grey 5x3 mean', 'grey 5x3 std']

    save_intermediate_results = False

    experiment_results = []

    # mutithreading variables
    coreCount = multiprocessing.cpu_count()
    processCount = (coreCount - 1) if coreCount > 1 else 1

    # main process to get the relevant values
    def process_experiment_folder( self, experiment_folder, experiment_pos, experiment_count=1, verbose=False ):

        print(' {:02d}/{:02d}: processing folder "{}" ...'.format(experiment_pos, experiment_count, experiment_folder))

        working_directory = self.experiments_directory + os.sep + experiment_folder + os.sep
        result_df = pd.DataFrame(columns = self.pandas_columns)
        # create output folder
        output_directory = working_directory + '/cv/'
        if not os.path.exists(output_directory):
            os.mkdir(output_directory)

        # counting available CSV files
        image_count = 0
        for file in os.listdir(working_directory):
            if ( file.endswith( ".jpg" ) ):
                image_count += 1

        # processing CSV files
        result_list          = [] # list containing results of every single image
        image_pos = 0
        for file in os.listdir(working_directory):
            if ( file.endswith( ".jpg" ) ):
                image_pos += 1
                if verbose: print('  {:02d}: processing file {} ({:02d} of {:02d})'.format( experiment_pos, file, image_pos, image_count ))
                # basic file handling
                # expecting a filename as follows: {experiment}_[a-e]_[1-9]
                # eg: 0-0_a_1.jpg, HG_c_8.jpg
                basename = os.path.splitext(os.path.basename(file))[0]

                # open image
                image = cv2.imread(working_directory + os.sep + file)
                height, width = image.shape[:2]

                # convert to grayscale
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                if self.save_intermediate_results: cv2.imwrite( output_directory + basename + '_gs.jpg', image)

                # enhance histogram in a similar manner as in ImageJ
                image = stretchHistogram(image, saturated=0.35)
                if self.save_intermediate_results: cv2.imwrite(output_directory + basename + '_eq.jpg', image)

                # set a threshold of 130 and binarise the image
                _, im_th = cv2.threshold(image, 130, 255, cv2.THRESH_BINARY)
                if self.save_intermediate_results: cv2.imwrite( output_directory + basename + '_th.png', cv2.bitwise_not(im_th) )

                # get the particles and their respective area
                contours, hierarchy = cv2.findContours(im_th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                areas = []
                contourCount = len(contours)
                for i in range(0, contourCount):
                    if cv2.contourArea(contours[i]) > 0:
                        areas.append(cv2.contourArea(contours[i]))

                # write to a dataframe and CSV
                if self.save_intermediate_results:
                    particle_df = pd.DataFrame()
                    particle_df = particle_df.append(areas, ignore_index=True)
                    particle_df.to_csv(output_directory + basename + '_psd.csv', index=False)

                a   = [] # list of sums of the particle sizes within given limits
                b   = [] # list of sums of the particle sizes to the given limit
                rop = [] # list of the "rate of passage" to the given limit
                rop_output = ''
                area_sum = sum(areas)

                for i in range(self.limitlen):
                    b.append(0)

                    if i == 0: lowerlimit = 0
                    else: lowerlimit = self.limits[i-1]

                    if i == len(self.limits): upperlimit = "max"
                    else: upperlimit = self.limits[i]

                    a.append( getarea(areas, lowerlimit, upperlimit) )
                    for j in range(i+1):
                        b[i] += a[j]

                    rop.append( 100 / area_sum * b[i] )
                    rop_output += str(round(rop[i],2)) + ", "

                maxsize = np.amax(area_sum)
                masked = round((100/(height*width)*area_sum), 2)
                d95 = getDx(95, rop, maxsize, self.limits)

                # grayscale analysis
                grey_5_3 = get_grey_values( im_th, row_count=3, col_count=5 )
                grey_2_2 = get_grey_values( im_th, row_count=2, col_count=2 )

                # generate table of the results of every image
                result_row = [basename] + rop + [100, maxsize, masked, d95, np.mean(grey_2_2), np.std(grey_2_2), np.mean(grey_5_3), np.std(grey_5_3)]
                result_list.append(result_row)
                result_df = result_df.append(pd.Series(result_row, index=self.pandas_columns), ignore_index=True)


        if self.save_intermediate_results:
            result_df.to_csv(output_directory + 'result.csv', index=False)

        if self.save_intermediate_results:
            experiment_tile_list = {} # dictionary containing results of a single specimen (set of 9 images)
            experiment_list      = {} # dictionary containing results of an 5 times repeated experiment (set of 5 x 9 images)

            # process intermediate results for every specimen within an experiment row
            for index, row in result_df.iterrows():
                basename_split = row['image'].split("_")
                key = basename_split[0] + '_' + basename_split[1]
                if not key in experiment_tile_list:
                    experiment_tile_list[key] = {
                        'd95':           row['d95'],
                        'grey 2x2 mean': row['grey 2x2 mean'],
                        'grey 5x3 mean': row['grey 5x3 mean']
                    }
                else:
                    experiment_tile_list[key]['d95']           += row['d95']
                    experiment_tile_list[key]['grey 2x2 mean'] += row['grey 2x2 mean']
                    experiment_tile_list[key]['grey 5x3 mean'] += row['grey 5x3 mean']

            for key, row in experiment_tile_list.items():
                experiment_tile_list[key]['d95']           = row['d95'] / 9
                experiment_tile_list[key]['grey 2x2 mean'] = row['grey 2x2 mean'] / 9
                experiment_tile_list[key]['grey 5x3 mean'] = row['grey 5x3 mean'] / 9

            #TODO save as csv

        result = {  'experiment':   experiment_folder,
                    'log(d95)':     math.log10(result_df['d95'].mean()),
                    'grey 2x2 mean std': result_df['grey 2x2 std'].mean(),
                    'grey 5x3 mean std': result_df['grey 5x3 std'].mean() }
        print(' {:02d}/{:02d}: finished "{}" ...'.format(experiment_pos, experiment_count, experiment_folder))
        return result

    def append_result(self, result_dict):
        self.experiment_results.append( result_dict )

    def __init__( self, save_intermediate_results=False ):
        self.save_intermediate_results = save_intermediate_results

        # get the directory containing the folders with the experiments
        self.experiments_directory = filedialog.askdirectory(title='Please select the directory containing the experiment directories...')

        if os.path.isdir(self.experiments_directory):
            # counting folders
            experiment_count = 0
            for folder in os.listdir(self.experiments_directory):
                folder_path = self.experiments_directory + os.sep + folder + os.sep
                if os.path.isdir(folder_path):
                    experiment_count += 1

            print('Start processing {:02d} folders using {} threads'.format( experiment_count, self.processCount))

            # iterate over all folders
            pool = multiprocessing.Pool(self.processCount)
            experiment_pos = 0
            for folder in os.listdir(self.experiments_directory):
                folder_path = self.experiments_directory + os.sep + folder + os.sep
                if os.path.isdir(folder_path):
                    experiment_pos += 1
                    pool.apply_async(self.process_experiment_folder, args=(folder, experiment_pos, experiment_count), callback = self.append_result)

            pool.close()
            pool.join()

            print("\nFinished processing all experiments:\n")

            # finalize, save and show the result table
            experiment_results_df = pd.DataFrame()
            experiment_results_df = experiment_results_df.append(self.experiment_results, ignore_index=True)
            experiment_results_df = experiment_results_df.sort_values(by=['experiment'])
            experiment_results_df.to_csv(self.experiments_directory + os.sep + 'frosting result.csv', index=False)

            print(experiment_results_df)

            print("\nDisclaimer:")
            print("These results are not identical with the original processing pipeline due to the differences in the historgram stretching algorithm!")
            print("To re-evaluate the original results, use the ImageJ/PHP pipeline. (or maybe fix the histogram stretching ;))")

# start process
if __name__ == '__main__':
    programInfo()

    # loading class glass_frosting_analysis

    # Change "save_intermediate_results" to True to get all intermediate results like images and CSVs
    # These files will be stored in the folder "cv"
    glass_frosting_analysis(save_intermediate_results=False)
