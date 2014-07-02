# MoveAndBenchmark

This is a simple python script for doing the moving files between a source disk and a destination disk, deleting files older than a specified date on the destination disk, and benchmarking the write speed of the source disk. We use it for keeping filesystems clean on our data acquisition computers where we have a small, fast, SSD array and a large, slow, hard drive array. This script:

 - Deletes files older than X (default: 30) days on destination
 - (Optional) Moves files from source to destination
 - (Optional) Benchmarks the write speed of source
 - Logs the amount of data moved and the write speed
 
 This allows us to empty the SSD every day and delete files off the hard drive often enough so that there is space to write new data.  It uses the [Parkdale command line tool](http://thesz.diecru.eu/content/parkdale.php) to do the write speed benchmarking. We benchmark to see if SSD RAID 0 arrays without TRIM enabled are degrading in performance.
 
 Use this program at your own risk! If you set parameters incorrectly, it can wipe your whole disk! Make sure you understand what you are doing before you run it.