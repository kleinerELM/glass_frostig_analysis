# Glass frosting analysis

These scripts can be used to analyse the quality of frosted glasware as described in the paper `Optimization and semi-automatic evaluation of a frosting process for a soda lime silicate glass based on phosphoric acid`.

## Example image

<img src="./example images/0-0_e_4.jpg" alt="Typical image with a bad frosting result" width="300px">

Typical image with a bad frosting result as used in the dataset in the afore mentioned paper. More example image can be found in the folder `.\example images\` in this repository.

## Method used in the paper
The data in the paper were generated using an ImageJ macro `MAKRO.ijm` to calculate the size of the tips of the crystal-like structures and the mean grey values of the areas. The class `Calculate_Mean` is necessary to run the greyscale analysis. The script asks for the directory containing the images from the microscope. The resulting CSV files were stored within a child-folder called csv.
Afterwards these raw data can be evaluated using the PHP script `PSA.php` which was called from command line in this way: `.\PSA.php?dir=DIRECTORY` (replace DIRECTORY with the path of the resulting csv data of the specimen).

The files mentioned can be found in the folder `.\original scripts\` in this repository.

Requirements:
* ImageJ / Fiji
  * installed makro Calculate_Mean
* locally installed PHP 5.6

## Important
The results require some more processing which was originally done using a spreadsheet

## Method translated to Python 3
Since the proposed method is hard to follow, the method will be translated to an easy to run python script.

### Requirements
 * Python 3.x
 * Python packages:
   * opencv-python
   * numpy
   * tkinter
   * pandas
   * math
   * subprocess
   * multiprocessing

Install these packages using

    pip install opencv-python numpy tkinter pandas math subprocess multiprocessing

### Expected folder structure

This is the folder structure used for the dataset of the paper "`Optimization and semi-automatic evaluation of a frosting process for a soda lime silicate glass based on phosphoric acid`", which is expected by the python script. The script asks for the `Experiments` folder, containing the other folders. The Names of the subfolders can be changed freely.
For some exported CSVs the scripts expects 9 images per specimen.

 * Experiments
  * 0-0
    * 0-0_a_1.jpg
    * 0-0_a_2.jpg
    * ...
    * 0-0_a_9.jpg
    * 0-0_b_1.jpg
    * 0-0_b_2.jpg
    * ...
    * 0-0_b_9.jpg
  * 0-1
    * 0-1_a_1.jpg
    * ...
  * 0-2
    * 0-2_a_1.jpg
    * ...
  * 0-3
    * 0-3_a_1.jpg
    * ...

### Options

Change `save_intermediate_results` to `True` to get all intermediate results like images and CSVs. These files will be stored in the folder `cv`.

    glass_frosting_analysis(save_intermediate_results=True)

### Disclaimer
The results processed with the python script are not identical with the results from the original processing pipeline due to the differences in the histogram stretching algorithm!
To re-evaluate the original results, use the ImageJ/PHP pipeline. Or maybe fix the histogram stretching algorithm to get the same results as ImageJ.
Nevertheless, the evaluation has to be redone in any case for different specimens, since the images will slightly change due to different microscope parameters.