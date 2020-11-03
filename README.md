# Glass frosting analysis

These scripts can be used to analyse the quality of frosted glasware as described in the paper `Optimization and semi-automatic evaluation of a frosting process for a soda lime silicate glass based on phosphoric acid`.

## Method used in the paper
The data in the paper were generated using an ImageJ macro `MAKRO.ijm` to calculate the size of the tips of the crystal-like structures and the mean grey values of the areas. The class `Calculate_Mean` is necessary to run the greyscale analysis. The script asks for the directory containing the images from the microscope. The resulting CSV files were stored within a child-folder called csv.
Afterwards these raw data can be evaluated using the PHP script `PSA.php` which was called from command line in this way: `.\PSA.php?dir=DIRECTORY` (replace DIRECTORY with the path of the resulting csv data of the specimen).
Finally, these data were examined using a spreadsheet.

The files mentioned can be found in the folder `.\original scripts\`

Requirements:
* ImageJ / Fiji
  * installed makro Calculate_Mean
* locally installed PHP 5.6

## Method translated to Python 3
Since the proposed method is hard to follow, the method will be translated to a easy to run python script.

Requirements:
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

`pip install opencv-python numpy tkinter pandas math subprocess multiprocessing`

### Disclaimer:
The results processed with the python script are not identical with the original processing pipeline due to the differences in the histogram stretching algorithm!
To re-evaluate the original results, use the ImageJ/PHP pipeline. Or maybe fix the histogram stretching algorithm to get the same results as ImageJ.
Nevertheless, the evaluation has to be redone in any case for different specimens, since the images will slightly change due to different microscope parameters.