# Astronomy
[![astropy](http://img.shields.io/badge/powered%20by-AstroPy-orange.svg?style=flat)](http://www.astropy.org/)
* Basic Link for source code
    * https://docs.astropy.org/en/stable/generated/examples/coordinates/plot_obs-planning.html
 
## General Program Idea
I want a program that can handle a few scenarios.  Basically I want to give it a 
location and an object (or list) and then have it give me a plot or some AltAz
numbers for when and where the object would be available
#### Basic program
* :x: command line location and object
* :heavy_check_mark: return AltAZ table at a few key times in HTML document 
    * :heavy_check_mark: key times meaning +10deg above horizon, 30deg, 45deg
    * :heavy_check_mark: altitude at key times??
* :heavy_check_mark: email document option
#### Upgrade 1
* :heavy_check_mark:get date and use that to show times of sun
    * :heavy_check_mark: sunset etc
* :heavy_check_mark:also return basic stats on object
#### Upgrade 2
* :heavy_check_mark: add graphic plots
#### Upgrade 3
* :heavy_check_mark: take list of objects and show data in plot(s) and tables for printing
    * :heavy_check_mark: show which objects on that day will be worth viewing
* add basic stats and and links
    * wikipedia data, image search
#### Upgrade 4
* this enhancement will be delayed a while as I work on other parts.  I am prioritizing aesthetic enhancements first. 
* make it work as an executable with pyinstaller
* https://ourcodeworld.com/articles/read/273/how-to-create-an-executable-exe-from-a-python-script-in-windows-using-pyinstaller
#### Upgrade 5
* :x: it occurs to me that I should also make the background black and the text white as the intention is for this to be viewied at night or in some darkeness where as if I print it out, I would reverse that.  hmm, perhaps I need a printing out option.
* :x: this will need to be described further
#### Upgrade 6 - Ideas from tonights (10-29) club board meeting
* :x: add link from object name to nasa page for each messier object
* :heavy_check_mark: add alt az link to wikipedia and a chart explaining AZ map to compass points
* :x: add column headers to each hour block
#### Upgrade 7
* :heavy_check_mark: find calc api or something to link lunar illumination / phase
#### Upgrade 8
* add auto convert to pdf with active links
* add section with definition of my terms at the bottom of the page
## Brainstorming
* accuweather has lots of info
    * https://developer.accuweather.com/apis
    * locations to get geo coords if needed
        * https://developer.accuweather.com/accuweather-locations-api/apis
    * get current conditions
        * https://developer.accuweather.com/accuweather-current-conditions-api/apis
    


