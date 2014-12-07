__Autopointer__
========
Introduction
------------
Autopointer is a python daemon that resolve starfields images take from a telescope and show in a web page where is pointing that telescope. Also shows several astronimical data in realtime (Local Standard Time, sun and moon position, etc ...).

This software use pyephem and astrometry.net thus you have to have installed in your system.

__Installing__
----------
Download and put in a directory of your election. Edit autopointer.cfg and adapt to your needs some parameters.
Mandatory changes are:
```python
#WORK HOME
home_dir=/home/nacho/work/var/autopointer
telescopes=TELESCOPE1,TELESCOPE2,TELESCOPE3
```
Then define your telescope(s)

```python
[TELESCOPE1]
label=Albert
url=http://localhost/pointer/test/m81.png
solve_params=-D tmp/ -2 -p --overwrite -z 4 -y -g -l 60 -H 6 -u app
```
Be sure that last telescope image is available using that url.

Then make a sympolic link from home_dir to your webserver document root. 

i.e. 
```python
sudo ln -s /home/nacho/work/var/autopointer /var/www/html/autopointer
```
That is!

__Use__
-------
visit your web server link


