You are working with the files stored in the main directory  “label_check”. 
Path to this folder is : “/xxxx/xxxxxxxxx/xxxxxxxx/xxxxx/xxxxx_xxxxxx/”.

Input number one is the directory “260223_dme_predictions “, located in the main directory “label_check”. Directory “260223_dme_predictions” contains 100 sub-directories. Each sub-directory has a unique name with containing either ID (for example 22471894”) or ID and unique has (for example 22471894-2a6fe87687e95df57d0e3c53023d2d76e4531c5c).

Each sub-directory contains a .json file. Although  the content of each .json file in each sub-directory is unique, all .json files in all sub-folders have the same name “metadata”. You need to treat each .json file as a unique instance reletaed only to the sub-directory in which this .json file is located. 

The example of the content of the .json file in this folder:
{
  "documentType": {
    "id": "2",
    "name": "RECIPES"
  },
  "confidence": 0.999971778836855,
  "issueDate": {"value": "", "iso": "unknown"},
  "documentLanguage": {"value": "english", "code": "en"}
}

Input number two is the .xlsx file called “list_of_docs” located in the same main directory.
This list includes a link in the column A and the label of the document from that link in the column B.
For example:
https://www.xxxxxxxx.com/en/document/view/00000000000/xxx-xxxxxxx-xxxxxxxx-xxx-feb-2025 in A1 has “MAGAZINE” as label in the column B. The document ID is defined as the numeric string immediately following the view/ segment of the URL in the column A.

Part one of the analysis includes extracting the data from the sub-directories and respective .json files inside of them. You need to complete following steps.
Iterate through the “260223_dme_predictions” directory. For each sub-folder, extract data as follows:
-	Extract the document ID from the name of the each sub-directory. To do this truncate the string at the first hyphen (-) and keep only the leading numeric ID (e.g., 22471894-2a6fe87687e95df57d0e3c53023d2d76e4531c5c) becomes 22471894)
-	Extract the nessessary information from the .json files: id, name and confidence Eg. 2, RECIPES, 0.999971778836855. 
-	Sibmine the outputs of the previous two steps into one as “sub-derectory id; id from the json file, name from the json file and confidence from the json file.
The example of the output as reference: 22471894, 2, RECIPES, 0.999971778836855#

Part two of the analysis includes extracting the reference data from the list_of_docs.xslx file in the same main directory. You need to complete following steps:
-	Parse the unique numeric document ID from the URLs in Column A (the string of digits following /view/
-	Extract the corresponding document label from Column B.

Part three includes merging of the outputs of part one and part two. Compelte the following steps:
-	Perform a Left Join to merge the results from Part 1 (Machine Predictions) and Part 2 (Human Labels).
-	Use the document ID as a join key 
-	The Machine Prediction data (part 1 of the analysis) must be the "Left" table
-	ave the combined results as a .csv with these exact headers: doc_id_mc, label_id_mc, label_name_mc, label_confidence_temy, doc_id_anna, doc_label_anna

Part four: completing of the activity
Once the processing is complete, the script must provide a terminal summary for quality control:
-	Print "Successfully processed X sub-folders, failed Y", where X will stand for the amount of processed .json files in folders, and Y will stand for the amount of failed to process .json files. 
-	If any .json files were failed to process – print their filenames.

Provide a python code for this analysis.





