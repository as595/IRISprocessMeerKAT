# ---------------------------------------------------------------------
# History
# [200717 - Anna Scaife] : created
# ---------------------------------------------------------------------

import os,sys
import time


# options for debugging purposes
precal = True
runcal = True
slfcal = True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------

def get_jobid(filename):

	tmpfile = open(filename,"r")
	items = tmpfile.readline().split()
	if len(items) > 3:
		for item in items: item.rstrip(',').rstrip(']').lstrip('[')
		jobid = items[2:]
	else:
		jobid = items[-1]
	tmpfile.close()

	return jobid

# ---------------------------------------------------------------------

def get_status(filename):

	finished = False; success = False
	tmpfile = open(filename,"r")
	output = tmpfile.readline().split(';')[0].split('=')[-1]
	if output=="Done":
		finished = True
		success = True
	elif output=="Failed":
		finished = True
		success = False
	tmpfile.close()

	return finished, success

# ---------------------------------------------------------------------

def run_precal():

	# submit job:
	os.system("dirac-wms-job-submit meerkat_precal.jdl > .tmp \n")
	jobid_precal = get_jobid('.tmp')
	print("Running precal: "+jobid_precal)

    # get job status:
	while True:
		os.system("dirac-wms-job-status "+jobid_precal+" > .tmp\n")
		finished, success = get_status('.tmp')

		if finished:
			break

    # check status:
	if success:
		print("precal:", success)

		# update config file:
		os.system("dirac-wms-job-get-output "+jobid_precal+" \n")
		os.system("mv "+jobid_precal+"/myconfig* .tmp")
		for i, line in enumerate(open('.tmp')):
			if line.find("bpassfield")>-1: bpassfield = line.split()[-1]
			if line.find("fluxfield")>-1: fluxfield = line.split()[-1]
			if line.find("phasecalfield")>-1: phasecalfield = line.split()[-1]
			if line.find("targetfields")>-1: targetfields = line.split()[-1]
			if line.find("extrafields")>-1: extrafields = line.split()[-1]

		os.system("mv myconfig.txt .tmp \n")
		configfile = open('myconfig.txt',"w")
		for i, line in enumerate(open('.tmp')):
			if line.find("bpassfield")>-1: 
				tmp = line.split()[-1]
				line = line.replace(tmp,bpassfield)
			if line.find("fluxfield")>-1: 
				tmp = line.split()[-1]
				line = line.replace(tmp,fluxfield)
			if line.find("phasecalfield")>-1: 
				tmp = line.split()[-1]
				line = line.replace(tmp,phasecalfield)
			if line.find("targetfields")>-1: 
				tmp = line.split()[-1]
				line =line.replace(tmp,targetfields)
			if line.find("extrafields")>-1: 
				tmp = line.split()[-1]
				line = line.replace(tmp,extrafields)
			configfile.write(line)
				
		configfile.close()
		os.system("rm -r "+jobid_precal+" \n")
		os.system("rm -r .tmp \n")

	else:
		print("precal:", success)
		print("Check logs to determine error. JobID: "+jobid_precal)
		sys.exit()


	return success

# ---------------------------------------------------------------------

def run_runcal():

	# submit job:
	os.system("dirac-wms-job-submit meerkat_runcal.jdl > .tmp \n")
	jobid_runcal = get_jobid('.tmp')
	print("Running runcal: "+" ".join(jobid_runcal))
	
    # get job status:
	while True:
		finished, success = [], []
		for jobid in jobid_runcal:
			jobid = jobid.rstrip(',').rstrip(']').lstrip('[')
			os.system("dirac-wms-job-status "+jobid+" > .tmp\n")
			f, s = get_status('.tmp')
			finished.append(f)
			success.append(s)

		if all(finished):
			break

    # check status:
	if all(success):
		print("runcal:", success[0])

		# update config file:
		os.system("dirac-wms-job-get-output "+jobid+" \n")
		os.system("mv "+jobid+"/myconfig* .tmp")
		for i, line in enumerate(open('.tmp')):
			if line.find("fieldnames")>-1: os.system('echo "'+line+'" >> myconfig.txt \n')
		os.system("rm -r "+jobid+" \n")

	else:
		print("runcal: False")
		print("Check logs to determine error.")
		sys.exit()

	return

# ---------------------------------------------------------------------

def run_slfcal():

	# submit job:
	os.system("dirac-wms-job-submit meerkat_slfcal.jdl > .tmp \n")
	jobid_slfcal = get_jobid('.tmp')
	print("Running slfcal: "+jobid_slfcal)
	
    # get job status:
	while True:
		os.system("dirac-wms-job-status "+jobid_slfcal+" > .tmp\n")
		finished, success = get_status('.tmp')
		if finished:
			break

    # check status:
	if success:
		print("slfcal:", success)
	else:
		print("slfcal:", success)
		print("Check logs to determine error. JobID: "+jobid_slfcal)
		sys.exit()

		os.system("rm .tmp \n")

	return


# ---------------------------------------------------------------------
# ---------------------------------------------------------------------


if __name__ == '__main__':

	start = time.time()

	if precal: run_precal()
	if runcal: run_runcal()
	if slfcal: run_slfcal()

	end = time.time()

	print("Pipeline complete")
	print("Run time"+str(end-start)+" seconds")
