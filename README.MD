# Astronomy
:EMOJICODE:
* Basic Link for source code
    * https://docs.astropy.org/en/stable/generated/examples/coordinates/plot_obs-planning.html
 
## General Program Idea
I want a program that can handle a few scenarios.  Basically I want to give it a 
location and an object (or list) and then have it give me a plot or some AltAz
numbers for when and where the object would be available
#### Basic program
* command line location and object
* :heavy_check_mark: return AltAZ table at a few key times in HTML document :heavy_check_mark:
    * key times meaning +10deg above horizon, 30deg, 45deg
    * altitude at key times??
* email document option
#### Upgrade 1
* get date and use that to show times of sun
    * sunset etc
* also return basic stats on object
#### Upgrade 2
* add graphic plots
#### Upgrade 3
* take list of objects and show data in plot(s) and tables for printing
    * show which objects on that day will be worth viewing
* add basic stats and and links
    * wikipedia data, image search
#### Upgrade 4
* make it work as an executable with pyinstaller
* https://ourcodeworld.com/articles/read/273/how-to-create-an-executable-exe-from-a-python-script-in-windows-using-pyinstaller

## Brainstorming
* accuweather has lots of info
    * https://developer.accuweather.com/apis
    * locations to get geo coords if needed
        * https://developer.accuweather.com/accuweather-locations-api/apis
    * get current conditions
        * https://developer.accuweather.com/accuweather-current-conditions-api/apis
    


# Python readme suggestions
* https://www.makeareadme.com/
* https://guides.github.com/features/mastering-markdown/
* https://github.com/ikatyang/emoji-cheat-sheet/blob/master/README.md
## Project should include
* What your project does
* How to install it
* Example usage
* How to set up the dev environment
* How to ship a change
* Change log
* License and author info