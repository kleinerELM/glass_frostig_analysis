// Macro for ImageJ 1.45s for Windows, requires makro "Calculate_Mean"
// written by Florian Kleiner 2012

macro "MattAnalyse" {
    dir = getDirectory("Choose a Directory ");
    list = getFileList(dir);
    setBatchMode(true);
    for (i=0; i<list.length; i++) {
        path = dir+list[i];
        showProgress(i, list.length);
        if (!endsWith(path,"/")) open(path);
        if (nImages>=1) {
	    filename = getTitle();
            width = getWidth();
            height = getHeight();

            // particle sizing
            run("8-bit");
            run("Enhance Contrast", "saturated=0.35");
            run("Apply LUT");
            setThreshold(130, 255, "black & white");
            run("Convert to Mask");
            run("Set Measurements...", "area redirect=None decimal=3");
            run("Analyze Particles...", "size=0-Infinity circularity=0.00-1.00 show=Nothing display clear");
            selectWindow("Results");
            saveAs("Results", dir+"csv\\"+substring(filename, 0, lengthOf(filename)-4)+".csv");
            save(dir+"csv\\"+filename);

            // particle size distribution
            for(j=0; j<= width-1; j+) {
                makeRectangle(0, 0, 693, 772);
                run("Calculate Mean");
                makeRectangle(693, 0, 693, 772);
                run("Calculate Mean");
                makeRectangle(1386, 0, 693, 772);
                run("Calculate Mean");
                makeRectangle(0, 772, 693, 772);
                run("Calculate Mean");
                makeRectangle(693, 772, 693, 772);
                run("Calculate Mean");
                makeRectangle(1386, 772, 693, 772);
                run("Calculate Mean");
            }
            selectWindow("Log");
            saveAs("Text", dir+"csv\\gs"+substring(filename, 0, lengthOf(filename)-4)+".txt");
            print("\\Clear");
            close();
        }
    }
}
