#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import commands,os, sys,glob,time
import datetime
import ConfigParser
import simplejson
from daemon import runner
import ephem
import numpy as np

class pointerClass:

	def __init__(self):
		#General paths
		binpath=os.path.realpath(sys.argv[0])
		configpath=os.path.dirname(binpath)
		self.cfg = ConfigParser.ConfigParser()
		self.cfg.read(configpath+"/autopointer.cfg")
		self.chkConfig()
		self.general=dict(self.cfg.items('GENERAL'))
		if not os.path.exists(self.general['base_dir']):
			os.makedirs(self.general['base_dir'])	
			os.makedirs(self.general['base_dir']+'/tmp')
			os.makedirs(self.general['log_dir'])
		if not os.path.isfile(self.general['base_dir']+'/index.html'):
			cmd="cp -av "+configpath+"/html/index.html "+self.general['base_dir']
			res=commands.getoutput(cmd)
			print res
		if not os.path.isfile(self.general['base_dir']+'/style.css'):
			cmd="cp -av "+configpath+"/html/style.css "+self.general['base_dir']
			res=commands.getoutput(cmd)
			print res
		if not os.path.exists(self.general['base_dir']+'/test'):
			cmd="cp -av "+configpath+"/test "+self.general['base_dir']
			res=commands.getoutput(cmd)
			print res

	        self.stdin_path = '/dev/null'
		if float(self.general["debug"])==1:
		        self.stdout_path = '/dev/tty'
			self.stderr_path = '/dev/tty'
		else:
		        self.stdout_path = '/dev/null'
			self.stderr_path = self.general["log_dir"]+'/pointer.log'
		self.pidfile_path =  self.general["log_dir"]+'/pointerDaemon.pid'
	        self.pidfile_timeout = 5
		here = ephem.Observer()
		here.lat, here.lon, here.horizon  = str(self.general['lat']), str(self.general['lon']), str("00:00:00")
		here.elev = float(self.general['elev'])
		here.temp = 25e0
		here.compute_pressure()
		print("Observer info: \n", here)
		# setting in self
		self.here = here


	def dirs(self):
		pass

	def run(self):


		os.chdir(self.general['base_dir'])
		telescopes=self.general['telescopes'].split(',')
		sun=ephem.Sun()
		moon=ephem.Moon()
		print telescopes
		ra_dec_rot=[]
		for n,telescopeName in enumerate(telescopes):
			ra_dec_rot.append(('-','-','-'))
        	while True:	
			log=self.getjson()
			try:
				print log['TELESCOPE']
			except:
				print "INIT JSON"
				log['TELESCOPE']=[]
				ra_dec_rot=[]
				for n,telescopeName in enumerate(telescopes):
					log['TELESCOPE'].append({})
					ra_dec_rot.append(('-','-','-'))

			T=datetime.datetime.utcnow()	
			log['DATE']=T.strftime('%d/%m/%Y %H:%M:%S')
			print T.strftime('%d/%m/%Y %H:%M:%S')
			self.here.date=ephem.date(T.strftime('%Y/%m/%d %H:%M:%S'))
			print "LST:",str(self.here.sidereal_time())
			log['LST']=str(self.here.sidereal_time())

			sunrise=self.here.next_rising(sun)
			sunset=self.here.next_setting(sun)
			
			moonrise=self.here.next_rising(moon)
			moonset=self.here.next_setting(moon)

			moonfull=ephem.next_full_moon(self.here.date)
			moonnew=ephem.next_new_moon(self.here.date)
			moonphase=ephem.next_new_moon(self.here.date)

			self.here.date=ephem.date(T.strftime('%Y/%m/%d %H:%M:%S'))
			moon.compute(self.here)
			sun.compute(self.here)
			print "SUN:",sunrise,sunset
			print "MOON:",moonrise,moonset
			print "MOON NEXT:",moonfull,moonnew
			print "MOON PHASE",moon.moon_phase

			log['SUNRISE']=str(sunrise)
			log['SUNSET']=str(sunset)
			sunalt=round(sun.alt*180/np.pi,1)
			sunaz=round(sun.az*180/np.pi,1)
			log['SUNALT']=str(sunalt)
			log['SUNAZ']=str(sunaz)
			if sunalt>0:
				log['twilight']='DAY'
			if sunalt<0:
				log['twilight']='CIVIL'
			if sunalt<-6:
				log['twilight']='NAUTICAL'
			if sunalt<-18:
				log['twilight']='NIGHT'



			log['MOONRISE']=str(moonrise)
			log['MOONSET']=str(moonset)
			log['FULLMOON']=str(moonfull)
			log['NEWMOON']=str(moonnew)
			log['MOONPHASE']=str(round(moon.moon_phase,3)*100)
			log['MOONRA']=str(moon.ra)
			log['MOONDEC']=str(moon.dec)
			moonalt=round(moon.alt*180/np.pi,1)
			moonaz=round(moon.az*180/np.pi,1)
			log['MOONALT']=str(moonalt)
			log['MOONAZ']=str(moonaz)



			for n,telescopeName in enumerate(telescopes):
				print "Checking telescope:",telescopeName,n
				telescope=dict(self.cfg.items(telescopeName))
				cmd="wget -c "+telescope['url']
				res=commands.getoutput(cmd)
				print res
				imageFile=os.path.basename(telescope['url'])
				dest_imageFile=telescopeName+'.jpg'
				dir_dest=self.general['base_dir']+"/"+telescopeName
				print dir_dest
				if not os.path.exists(dir_dest):
					os.makedirs(dir_dest)
				res=commands.getoutput("mv "+dir_dest+"/"+dest_imageFile+" "+dir_dest+"/"+dest_imageFile+".old")
				print res
				res=commands.getoutput("mv "+imageFile +" "+dir_dest+"/"+dest_imageFile)
				if not os.path.isfile(dir_dest+"/"+dest_imageFile):
					continue
				fileDate=time.strftime("%Y/%m/%d %H:%M:%S",time.gmtime(os.path.getmtime(dir_dest+"/"+dest_imageFile)))
				#fileDate=time.ctime(os.path.getmtime(dir_dest+"/"+dest_imageFile))
				print "LAST IMAGE DATE",fileDate
				print res
				if not os.path.isfile(dir_dest+"/"+dest_imageFile+".old") or \
				   os.path.getsize(dir_dest+"/"+dest_imageFile)!=os.path.getsize(dir_dest+"/"+dest_imageFile+".old"):
					(name,RA_CENTER, DEC_CENTER,rotation)=self.astrometry(dir_dest+"/"+dest_imageFile,telescope['solve_params'])
					res=commands.getoutput("mv "+name+" "+dir_dest+"/"+dest_imageFile+'.fit')
					print res
					print fileDate
					print RA_CENTER, DEC_CENTER
					print rotation
					ra_dec_rot[n]=(RA_CENTER, DEC_CENTER,rotation)

				#UPDATE DATA

				(RA_CENTER, DEC_CENTER,rotation)=ra_dec_rot[n]
				if not RA_CENTER=='-':					
					#self.here.date=ephem.date(fileDate)
					a = ephem.FixedBody()
					a._ra = ephem.hours(RA_CENTER)
					a._dec = ephem.degrees(DEC_CENTER)
					a.compute(self.here)
					alt=round(float(a.alt)*180/np.pi,1)
					az=round(float(a.az)*180/np.pi,1)
					constellation=ephem.constellation(a)
				else:
					alt='-'
					az='-'
					constellation='-'
				RA_=RA_CENTER[:RA_CENTER.find('.')]
				DEC_=DEC_CENTER[:DEC_CENTER.find('.')]
				d={'NAME':telescopeName,'LABEL':telescope['label'],'DATE':fileDate,'RA':RA_,'DEC':DEC_, \
				'ALT':alt,'AZ':az,'CONSTELLATION':constellation,'ROTATION':rotation,'IMAGE':telescopeName+"/"+dest_imageFile}
				log['TELESCOPE'][n]=d


			self.recordjson(log)		
        		time.sleep(int(self.general['check_every']))

	def astrometry(self,img,params):
		cmd='solve-field  '+params+" "+img
		print cmd
		res=commands.getoutput(cmd)
		print res
	 	#for filename in glob.glob('/tmp/tmp.sanitized.*') :
	    	#	os.remove( filename ) 
		if res.find("Did not solve")>0:
			print "FAIL TO SOLVE"
			return 	("", "-", "-", "-")
		try:
			field_center=res[res.find("Field center: (RA H:M:S, Dec D:M:S) ="):].split('\n')[0]
			(RA_CENTER,DEC_CENTER)=field_center[39:-2].split(',')
			field_rotation=res[res.find("Field rotation angle:"):].split('\n')[0]
			#print field_rotation[28:-16]
			fits_info=res[res.find("Creating new FITS"):].split('\n')[0]
			#print "PPP"+fits_info[24:-4]+"PPP"
		except:
			print "FAIL TO SOLVE"
			return 	("", "-", "-", "-")

	  	#Remove tmp files
		if 0:
		    try:		
	  		for filename in glob.glob('/tmp/tmp.sanitized.*') :
	    			os.remove( filename ) 
	  		for filename in glob.glob('/tmp/tmp.fit.*') :
	    			os.remove( filename ) 
	  		for filename in glob.glob('/tmp/tmp.ppm.*') :
	    			os.remove( filename ) 

		    except:
			pass

		return 	(fits_info[24:-4], RA_CENTER, DEC_CENTER, field_rotation[28:-16])

	def chkConfig(self):
		for section in self.cfg.sections():
			print
			print "================ "+section+" ================"
			for item in self.cfg.items(section):
				print item

	def recordjson(self,jsn):
		filename=self.general['jsonfile']
		x = simplejson.dumps(jsn)
		statsDir=os.path.dirname(filename)
		if not os.path.exists(statsDir):
		    os.makedirs(statsDir)
	        fi=open(filename,"w")
		fi.write(x)
		fi.close()

	def getjson(self):
		filename=self.general['jsonfile']
		if not os.path.isfile(filename):
			print "NO EXISTS:",filename
		    	return {}
	        fi=open(filename,"r")
		obj=fi.read()
		fi.close()
		json_dict= simplejson.loads(obj)
		return json_dict
		
if __name__ == '__main__':
	checker=pointerClass()
	daemon_runner = runner.DaemonRunner(checker)
	daemon_runner.do_action()
	



