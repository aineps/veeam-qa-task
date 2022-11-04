# Veeam QA Task

Python script that synchronizes a source and replica folder and logs:
- File creation: If a new file is created
- File copying: If an existng file is modified and copied to the replica folder
- File deletion: If a file is deleted

The script includes two objects:
- Folder: a folder object including the folder's path and contents
- Sync: a sync object storing the sync methods
  - compare_root which starts the recursive loops for compare_folders and handles the overall printing to console
  - compare_folders which does the actual sync comparison for individual folders, recursive for subdirectories
  - write_log which does the logging for file actions (only files, but would be easy enough to extend to folder creation/copying/deleting)
  - copy_files (copies logs new files as created and edited, existing files as copied)
  - delete_files (deletes and logs deleted files)

The script takes two folder paths, the log file path and synchronization interval as console inputs and continues the synchronization indefinitely.
