from __future__ import print_function

import datetime
import errno
import os
import sys

import core
from core import logger, nzbToMediaDB
from core.nzbToMediaUtil import extractFiles, CharReplace, convert_to_ascii, get_nzoid
from core.nzbToMediaUtil import flatten, listMediaFiles, import_subs
from core.transcoder import transcoder
from libs.six import text_type


class Filechecker(object):


    def checkfiles(self, section, dirName, inputName=None, failed=False, clientAgent="manual", download_id=None, inputCategory=None, failureLink=None):
        cfg = dict(core.CFG[section][inputCategory])
        # auto-detect correct fork
        #fork, fork_params = autoFork(section, inputCategory)

        nzbExtractionBy = cfg.get("nzbExtractionBy", "Downloader")
        status = int(failed)
        if status > 0 and core.NOEXTRACTFAILED:
            extract = 0
        else:
            extract = int(cfg.get("extract", 0))

        if not os.path.isdir(dirName) and os.path.isfile(dirName):  # If the input directory is a file, assume single file download and split dir/name.
            dirName = os.path.split(os.path.normpath(dirName))[0]

        SpecificPath = os.path.join(dirName, str(inputName))
        cleanName = os.path.splitext(SpecificPath)
        if cleanName[1] == ".nzb":
            SpecificPath = cleanName[0]
        if os.path.isdir(SpecificPath):
            dirName = SpecificPath

        # Attempt to create the directory if it doesn't exist and ignore any
        # error stating that it already exists. This fixes a bug where SickRage
        # won't process the directory because it doesn't exist.
        try:
            os.makedirs(dirName)  # Attempt to create the directory
        except OSError as e:
            # Re-raise the error if it wasn't about the directory not existing
            if e.errno != errno.EEXIST:
                raise

        #if 'process_method' not in fork_params or (clientAgent in ['nzbget', 'sabnzbd'] and nzbExtractionBy != "Destination"):
        #if inputName:
        #    process_all_exceptions(inputName, dirName)
        #    inputName, dirName = convert_to_ascii(inputName, dirName)

            # Now check if tv files exist in destination.
            if not listMediaFiles(dirName, media=True, audio=False, meta=False, archives=False):
                if listMediaFiles(dirName, media=False, audio=False, meta=False, archives=True) and extract:
                    logger.debug('Checking for archives to extract in directory: {0}'.format(dirName))
                    core.extractFiles(dirName)
                    inputName, dirName = convert_to_ascii(inputName, dirName)

            if listMediaFiles(dirName, media=True, audio=False, meta=False, archives=False):  # Check that a video exists. if not, assume failed.
                flatten(dirName)

        # Check video files for corruption
        good_files = 0
        num_files = 0
        for video in listMediaFiles(dirName, media=True, audio=False, meta=False, archives=False):
            num_files += 1
            if transcoder.isVideoGood(video, status):
                good_files += 1
                import_subs(video)
        if num_files > 0:
            if good_files == num_files and not status == 0:
                logger.info('Found Valid Videos. Setting status Success')
                status = 0
                failed = 0
            if good_files < num_files and status == 0:
                logger.info('Found corrupt videos. Setting status Failed')
                status = 1
                failed = 1
                if 'NZBOP_VERSION' in os.environ and os.environ['NZBOP_VERSION'][0:5] >= '14.0':
                    print('[NZB] MARK=BAD')
                if failureLink:
                    failureLink += '&corrupt=true'

        elif nzbExtractionBy == "Destination":
            logger.info("Check for media files ignored because nzbExtractionBy is set to Destination.")
            if int(failed) == 0:
                logger.info("Setting Status Success.")
                status = 0
                failed = 0
            else:
                logger.info("Downloader reported an error during download or verification. Processing this as a failed download.")
                status = 1
                failed = 1
        else:
            logger.warning("No media files found in directory {0}. Processing this as a failed download".format(dirName), section)
            status = 1
            failed = 1



        return status









#definitions
# post-processing
def startproc(inputDirectory, inputName=None, status=0, clientAgent='manual', download_id=None, inputCategory=None, failureLink=None):
    if core.SAFE_MODE and inputDirectory == core.NZB_DEFAULTDIR:
        logger.error(
            'The input directory:[{0}] is the Default Download Directory. Please configure category directories to prevent processing of other media.'.format(
                inputDirectory))
        return [-1, ""]

    if not download_id and clientAgent == 'sabnzbd':
        download_id = get_nzoid(inputName)

    if clientAgent != 'manual' and not core.DOWNLOADINFO:
        logger.debug('Adding NZB download info for directory {0} to database'.format(inputDirectory))

        myDB = nzbToMediaDB.DBConnection()

        inputDirectory1 = inputDirectory
        inputName1 = inputName

        try:
            encoded, inputDirectory1 = CharReplace(inputDirectory)
            encoded, inputName1 = CharReplace(inputName)
        except:
            pass

        controlValueDict = {"input_directory": text_type(inputDirectory1)}
        newValueDict = {"input_name": text_type(inputName1),
                        "input_hash": text_type(download_id),
                        "input_id": text_type(download_id),
                        "client_agent": text_type(clientAgent),
                        "status": 0,
                        "last_update": datetime.date.today().toordinal()
                        }
        myDB.upsert("downloads", newValueDict, controlValueDict)


    # auto-detect section

    if inputCategory is None:
        inputCategory = 'UNCAT'
    usercat = inputCategory
    section = core.CFG.findsection(inputCategory).isenabled()
    if section is None:
        section = core.CFG.findsection("ALL").isenabled()
        if section is None:
            logger.error(
                'Category:[{0}] is not defined or is not enabled. Please rename it or ensure it is enabled for the appropriate section in your autoProcessMedia.cfg and try again.'.format(
                    inputCategory))
            return [-1, ""]
        else:
            usercat = "ALL"

    if len(section) > 1:
        logger.error(
            'Category:[{0}] is not unique, {1} are using it. Please rename it or disable all other sections using the same category name in your autoProcessMedia.cfg and try again.'.format(
                inputCategory, section.keys()))
        return [-1, ""]

    if section:
        sectionName = section.keys()[0]
        logger.info('Auto-detected SECTION:{0}'.format(sectionName))
    else:
        logger.error(
            "Unable to locate a section with subsection:{0} enabled in your autoProcessMedia.cfg, exiting!".format(
                inputCategory))
        return [-1, ""]

    cfg = dict(core.CFG[sectionName][usercat])

    extract = int(cfg.get("extract", 0))

    try:
        if int(cfg.get("remote_path")) and not core.REMOTEPATHS:
            logger.error(
                'Remote Path is enabled for {0}:{1} but no Network mount points are defined. Please check your autoProcessMedia.cfg, exiting!'.format(
                    sectionName, inputCategory))
            return [-1, ""]
    except:
        logger.error(
            'Remote Path {0} is not valid for {1}:{2} Please set this to either 0 to disable or 1 to enable!'.format(
                core.get("remote_path"), sectionName, inputCategory))

    inputName, inputDirectory = convert_to_ascii(inputName, inputDirectory)

    if extract == 1:
        logger.debug('Checking for archives to extract in directory: {0}'.format(inputDirectory))
        extractFiles(inputDirectory)

    logger.info("Calling Checker to check the Files and Convert them to mp4")


    result = Filechecker().checkfiles(sectionName, inputDirectory, inputName, status, clientAgent, download_id, inputCategory, failureLink)

    return result

def main():
    #START
    # Initialize the config
    section = None
    args = sys.argv
    core.initialize(section)

    logger.info("#########################################################")
    logger.info("## ..::[{0}]::.. ##".format(os.path.basename(__file__)))
    logger.info("#########################################################")

    # debug command line options
    logger.debug("Options passed into nzbToMedia: {0}".format(args))

    # Post-Processing Result
    result = [0, ""]
    status = 0

    #set arguments to variable args, because this is used as a default variable later



    #Argumente von Sabnzbd aufteilen
    # SABnzbd Pre 0.7.17
    if len(args) == core.SABNZB_NO_OF_ARGUMENTS:
        # SABnzbd argv:
        # 1 The final directory of the job (full path)
        # 2 The original name of the NZB file
        # 3 Clean version of the job name (no path info and ".nzb" removed)
        # 4 Indexer's report number (if supported)
        # 5 User-defined category
        # 6 Group that the NZB was posted in e.g. alt.binaries.x
        # 7 Status of post processing. 0 = OK, 1=failed verification, 2=failed unpack, 3=1+2
        clientAgent = 'sabnzbd'
        logger.info("Script triggered from SABnzbd")
        result = startproc(args[1], inputName=args[2], status=args[7], inputCategory=args[5], clientAgent=clientAgent,
                             download_id='')
        # SABnzbd 0.7.17+
    elif len(args) >= core.SABNZB_0717_NO_OF_ARGUMENTS:
        # SABnzbd argv:
        # 1 The final directory of the job (full path)
        # 2 The original name of the NZB file
        # 3 Clean version of the job name (no path info and ".nzb" removed)
        # 4 Indexer's report number (if supported)
        # 5 User-defined category
        # 6 Group that the NZB was posted in e.g. alt.binaries.x
        # 7 Status of post processing. 0 = OK, 1=failed verification, 2=failed unpack, 3=1+2
        # 8 Failure URL
        clientAgent = 'sabnzbd'
        logger.info("Script triggered from SABnzbd 0.7.17+")
        result = startproc(args[1], inputName=args[2], status=args[7], inputCategory=args[5], clientAgent=clientAgent, download_id='', failureLink=''.join(args[8:]))

    ##########here
    sys.exit(result)

if __name__ == '__main__':
    exit(main())