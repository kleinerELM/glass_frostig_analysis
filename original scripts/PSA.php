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



//sums areas
function getarea($lines, $lowerlimit, $upperlimit) {
    $result = 0;
    for($i = 0; $i < count($lines); $i++) {
        if ($upperlimit != "max") {
            if (($lines[$i] > $lowerlimit) && ($lines[$i] <= $upperlimit)) {
                $result += $lines[$i];
            }
        } else if ($lines[$i] > $lowerlimit) {
            $result += $lines[$i];
        }
    }
    return $result;
}

//function to get the Dx-value, eg. D95
function getDx($x, $rop, $maxsize) {
    global $limits;
    global $limitsize;

    $min = $minc = 0;
    $result = ">500";
    for($i = 0; $i < $limitsize; $i++) {
        if ($rop[$i] > $x) {
            $result = round(($limits[$i]-$min) / ($rop[$i]-$minc) * ($x-$minc) + $min);
            $i = $limitsize;
        }
        $min = $limits[$i];
        $minc = $rop[$i];
    }
    return $result == ">500" ? round(($maxsize-$min) / (100-$minc) * ($x-$minc) + $min) : $result;
}

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