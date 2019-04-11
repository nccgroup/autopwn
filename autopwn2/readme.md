# AutoPwn groups

The following sections will describe the various usages that AutoPwn has.
AutoPwn is a utility that helps automating the execution of tasks, predominantly aimed to help a pentester.

AutoPwn is aimed to start jobs. A job is the running of a particular tool/command. An assessment is a sequence of a number of jobs against a single target. 

## Assessment
An assessment is a group of tools that have a correlation. For example, an asssessment named SSL/TLS would run nmap with specific settings and testssl.
#### Parameters
- **name**
- **description** 
#### URLs
- /assessments 
    - [GET] returns all assessments
    - [POST] adds a new assessment 
- /assessments/&lt;id&gt;
    - [GET] returns the values of the requested assessment
    - [PUT] updates the assessment
    

## Tool
A Tool is a wrapper for a particular execution. Each tool has an command string that is specific for that tool. It contains named parameters that will be filled to run against a particular target. For example:
- Nmap SSL, is the command `nmap --script ssl-cert,ssl-enum-ciphers -p {port_number} {target} -oA {output_dir}/{timestamp}_{target}_nmap_ssl_scan`
- Nmap Full TCP, is the command `nmap -Pn -n -v6 -p- -sSCV -oA {output_dir}/{timestamp}_{target_name}_nmap_full {target}`
#### Parameters
- **name**
- description
- url, location of the base
- **command**, the commandline to be executed
- **stdout**, if the command also has commandline output that needs to be captured (default=False)
#### URLs
- /tools
    - [GET] returns all tools
    - [POST] adds a new tool
- /tools/&lt;id&gt;
    - [GET] returns the values of the requested tool
    - [PUT] updates the tool   
## Job
A job is the action scheduling to run a tool against a particular target. The parameters are filled from the settings. The parameters of a tool will be set when the job is created. It will use the values from the settings if particular parameters are not provided.
#### Parameters
- **tool**
- **command**, the filled command
- start_time, when the tool was started
- end_time, when the tool finished
- return_code, the return code of the command
#### URLs
- /jobs
    - [GET] returns all jobs
    - [POST] adds a new job
- /jobs/&lt;id&gt;
    - [GET] returns the values of the requested job
    - [PUT] updates the job
- /jobs/&lt;id&gt;/execute
    - [POST] starts the identified job, if post has parameters, incorporate them in template      
        - return 200 if job starts
        - return 400 if command still has parameters 
        
## Setting
Default settings that will be used for creating jobs
### URLs
- /settings
    - [GET] returns all settings
    - [POST]  adds a new setting
- /settings/&lt;id&gt;
    - [GET] returns the values of the requested setting
    - [PUT] updates the setting
    - [DELETE] deletes the setting
### Parameters
- **name**
- **value**
- example    
