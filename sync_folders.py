import os
import filecmp
import shutil
from stat import *

import time
import argparse

def parse_arguments():
    '''Takes the command line arguments and creates a sync object with them.'''
    parser = argparse.ArgumentParser(description="Script which syncs a source folder with a replica repeated at a given interval. Usage: sync_folders.py <source_path> <replica_path> --interval <interval (s)> --log_file <log file path>")
    
    parser.add_argument("src_path", type=str, help="Source file path")
    parser.add_argument("repl_path", type=str, help="Replica file path")
    parser.add_argument("--interval", type=int, help="Sync interval in seconds")
    parser.add_argument("--log_file", type=str, help="Log file path")

    args = parser.parse_args()
    return SyncObject(Folder(args.src_path), Folder(args.repl_path), args.interval, args.log_file, "test")


class Folder:
    '''
    This is a class for a folder.
    Attributes:
        - Path
        - File list
    '''
    def __init__(self, path, name=""):
        ''' Constructor for folder class'''
        self.name = name
        self.root_path = os.path.abspath(path)
        self.file_list = os.listdir(self.root_path)

class SyncObject:
    '''
    This is a class for a synchronization object. It handles the methods for synchronization.
    Attributes:
        - source (Folder): Source folder
        - replica (Folder): Replica folder
        - log_file (string) : Log file path
        - file_created_count (int)
        - file_copied_count (int)
        - file_deleted_count (int)
    Methods:
        - __init__: Constructor
        - compare_root: Start sync
        - compare_folders: Directory comparison, recursive
        - write_log: Writes actions to log file
        - copy_files: Creates and copies files
        - delete_files: Deletes files
    '''

    def __init__(self, source, replica, interval, log_file, name=""):
        '''Constructor for sync class. 
        Inputs: 
        - source: source folder (Folder)
        - replica: replica folder (Folder)
        - interval: interval time (int)
        - log_file: log file path (string)
        '''
        self.name = name
        self.source = source
        self.replica = replica
        self.interval = interval
        self.log_file = os.path.abspath(log_file)

        self.file_created_count = 0
        self.file_copied_count = 0
        self.file_deleted_count = 0

    def compare_root(self):
        '''Starts sync and logs this to console. Ends one sync by logging a count of file actions to the console and resetting the count. Repeats every interval'''
        while True:     
            # start sync
            print("Syncing " + self.source.root_path + " + " + self.replica.root_path)
            self.compare_folders(self.source.root_path, self.replica.root_path)
            print("Files created: " + str(self.file_created_count), "Files copied: " + str(self.file_copied_count), "Files deleted: " + str(self.file_deleted_count) + "\n")
            
            # clear after printing (if we want an overall count printed, just remove this)
            self.file_created_count = 0
            self.file_copied_count = 0
            self.file_deleted_count = 0

            # sleep for interval
            time.sleep(self.interval)

        
    def compare_folders(self, src, repl):
        '''Recursive folder comparison. Replica folder is modified accordingly to match source folder. 
        Inputs: 
            - src: source path (string)
            - repl: replica path (string). 
            '''
        compare_obj = filecmp.dircmp(src, repl) #compare with filecmp
        
        if compare_obj.common_dirs: 
            # nothing different at current level -> check subdirectories
            for folder in compare_obj.common_dirs:
                self.compare_folders(os.path.join(src, folder), os.path.join(repl, folder)) # call recursively for subdirectories
        
        if compare_obj.left_only:
            # source has files, replica does not
            self.copy_files(compare_obj.left_only, src, repl) 
        
        if compare_obj.right_only:
            # source does NOT have files, replica does
            self.delete_files(compare_obj.right_only, repl) 

        if compare_obj.diff_files: 
            # files are the same, but contents have changed
            self.copy_files(compare_obj.diff_files, src, repl, False)
    
    def write_log(self, type, file):
        '''Opens log file, appends file actions to log file and prints them to console. 
        Inputs: 
            - type: file action type (string)
            - file: file name (string)
        '''
        # log file opened in append mode, assuming we'd want continuous logging for continuous syncing
        # if we wanted one log file to only reflect one sync, opening in write mode in compare_root and handling only the writing in this function might be the easiest solution (each sync thus overwriting the previous log file).
        log_file = open(self.log_file, 'a')
        
        # log by action taken
        if type == "create":
            log_file.write("Created file: " + file + "\n")
            print("Created file: " + file)
        elif type == "copy":
            log_file.write("Copied file: " + file + "\n")
            print("Copied file: " + file)
        elif type == "delete":
            log_file.write("Deleted file: " + file + "\n")
            print("Deleted file: " + file)
        else:
            print("Error: Invalid file action") # pretty redundant for this script, but nonetheless best to have an error handler just in case
        
        log_file.close()


    def copy_files(self, file_list, src, dest, new=True):
        '''Copies files. A new file is logged as creation, an edited existing file is logged as copied. 
       Inputs: 
           - file_list: list of files to be copied (array)
           - src: source folder path (string)
           - dest: destination folder path (string)
           - new: whether the copied file is being created vs copied (Bool)
           '''
        for file in file_list:
            srcpath = os.path.join(src, os.path.basename(file))
            if os.path.isdir(srcpath):
                shutil.copytree(srcpath, os.path.join(dest, os.path.basename(file)))
                if new:
                    for file in os.listdir(srcpath):
                        self.file_created_count += 1
                        self.write_log("create", os.path.join(srcpath, file))
                else:
                    for file in os.listdir(srcpath):
                        self.file_copied_count += 1
                        self.write_log("copy", os.path.join(srcpath, file))
            else:
                shutil.copy2(srcpath, dest)
                if new:
                    self.file_created_count += 1
                    self.write_log("create", srcpath)
                else:
                    self.file_copied_count += 1
                    # log to file
                    self.write_log("copy", srcpath)

    def delete_files(self, file_list, folder):
        '''Deletes files. 
       Inputs: 
           - file_list: list of files to be deleted (array)
           - folder: path of folder files are in (string)
          '''
        for file in file_list:
            srcpath = os.path.join(folder, os.path.basename(file))
            if os.path.isdir(srcpath):
                for file in os.listdir(srcpath):
                    self.file_deleted_count +=1 
                    self.write_log("delete", os.path.join(srcpath, file))
                shutil.rmtree(srcpath)
            else:
                os.remove(srcpath)
                self.file_deleted_count += 1
                self.write_log("delete", srcpath)

if __name__=="__main__":

    # parse and run
    sync = parse_arguments()
    sync.compare_root()
