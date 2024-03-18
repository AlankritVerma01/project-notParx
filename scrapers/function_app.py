import azure.functions as func
import logging
import os
import requests

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

GENERATE_ID_URL = "https://notparx-prescriber-service.azurewebsites.net/api/createID/"
STATUS_UPDATE_URL = "https://notparx-prescriber-service.azurewebsites.net/api/update-status/"

# Tell backend that the csv has failed processing
def update_job_failed(old_file_name):
    body = {
        "old_file_name": old_file_name,
        "status": 'not processed'
    }
    requests.post(STATUS_UPDATE_URL, data = body)

# Tell backend that the csv has succeeded processing
def update_job_succeeded(old_file_name, new_file_name):
    body = {
        "old_file_name": old_file_name,
        "status": 'processed',
        "new_file_name": new_file_name,
    }
    requests.post(STATUS_UPDATE_URL, data = body)


@app.route(route="verifier")
@app.function_name(name="verifier")
async def verifier(req: func.HttpRequest) -> func.HttpResponse:
    # Note: imports have to be here or azure breaks
    import csv
    
    import site1
    import site2
    import site3
    import site4
    import site5
    import site6
    import site7
    import site8
    import site9
    import site10


    import uuid
    from io import StringIO

    # Disable webdriver manager logs
    import os
    os.environ['WDM_LOG'] = '0'

    from azure.identity.aio import DefaultAzureCredential
    from azure.storage.blob.aio import BlobServiceClient, BlobClient, ContainerClient

    logging.info('Python HTTP trigger function received a request.')

    # TODO restart on hitting 9 min time limit.

    # Create the BlobServiceClient object
    blob_service_client = BlobServiceClient.from_connection_string(os.environ['STORAGE_CONNECTION_STRING'])
    
    # Get csv name from passed args
    blob_name = req.params.get('csv_name')
    if not blob_name:
        try:
            req_body = req.get_json()
            blob_name = req_body.get('csv_name')
        except ValueError:
            pass

    if not blob_name:
        return func.HttpResponse(f"Missing identifier csv_name", status_code=400)

    # Download csv from azure
    download_client = blob_service_client.get_blob_client(container="csv-container", blob=blob_name)
    if (not download_client.exists()):
        update_job_failed(blob_name)
        return func.HttpResponse(
             "Couldn't find csv on server",
             status_code=404
        )
        
    download_stream = await download_client.download_blob()
    data = await download_stream.readall()
    
    base = []
    reader = csv.reader(data.decode("utf-8").splitlines())
    for row in reader:
        base.append(row)

    print(base)

    # Find required info columns
    FIRST_NAME_IND=-1
    LAST_NAME_IND=-1
    PROVINCE_IND=-1
    LICENSING_IND=-1
    COLLEGE_IND=-1
    STATUS_IND=-1
    try:
        for i in range(len(base[0])):
            col = base[0][i]
            if col is not None and col.strip() == "First Name":
                FIRST_NAME_IND = i
            if col is not None and col.strip() == "Last Name":
                LAST_NAME_IND = i
            if col is not None and col.strip() == "Province":
                PROVINCE_IND = i
            if col is not None and col.strip() == "Licence #":
                LICENSING_IND = i
            if col is not None and col.strip() == "Licensing College":
                COLLEGE_IND = i
            if col is not None and col.strip() == "Status":
                STATUS_IND = i
    except:
        logging.info('Failed to parse csv headers')
        update_job_failed(blob_name)
        return func.HttpResponse(
             "Failed to parse csv headers",
             status_code=500
        )

    if -1 in [FIRST_NAME_IND, LAST_NAME_IND, PROVINCE_IND, LICENSING_IND, COLLEGE_IND]:
        update_job_failed(blob_name)
        return func.HttpResponse(
             "Missing required csv headers (First Name, Last Name, Province, Licensing College, Licensing #)",
             status_code=400
        )
    
    base_res = []
    base_res.append(base[0][:])
    if STATUS_IND == -1:
        base_res[0].append("Status")
        STATUS_IND = len(base_res[0]) - 1
    
    scraping_strategy = {
        "BC": site1,
        "ON": site2,
        "SK": site3,
        "MB": site4,
        "PE": site5,
        "AB": site6,
        "NB": site7,
        "NL": site8,
        "NS": site9,
        "QC": site10
    }

    # Parse row by row
    for i in range(1,len(base)):
        try:
            base_res.append(base[i][:])
            while len(base_res[i]) <  max([FIRST_NAME_IND, LAST_NAME_IND, PROVINCE_IND, LICENSING_IND, COLLEGE_IND, STATUS_IND]) + 1:
                base_res[i].append("")
            
            # If row already has something in status column, don't reprocess it
            if base_res[i][STATUS_IND] != "":
                continue

            first_name = base_res[i][FIRST_NAME_IND].strip()
            last_name = base_res[i][LAST_NAME_IND].strip()
            province = base_res[i][PROVINCE_IND].strip()
            license_id = base_res[i][LICENSING_IND].strip()
            college = base_res[i][COLLEGE_IND].strip()
            status = "ERROR"

            # Verify row
            if province not in scraping_strategy:
                base_res[i][STATUS_IND] = "ERROR"
                continue
            status = scraping_strategy[province].get_status(first_name, last_name, license_id)

            # TODO: send verified practitioner to our backend
            if status == "VERIFIED":
                body = {
                    "firstName": first_name,
                    "lastName": last_name,
                    "province": province,
                    "college": college,
                    "licenseNum": license_id,
                    "status": status
                }
                requests.post(GENERATE_ID_URL, data = body)

            base_res[i][STATUS_IND] = status
            print(f"row i={i} status: {status}")

        except Exception as e:
            logging.info(f'Error during row i={i}. Error: {str(e)}')
            while len(base_res[i]) < STATUS_IND + 1:
                base_res[i].append("")
            base_res[i][STATUS_IND] = "ERROR"

    
    # Job complete - upload new csv
    filename = str(uuid.uuid1()) + ".csv"
    out_stream = StringIO(newline = '')
    writer = csv.writer(out_stream)
    for row in base_res:
        writer.writerow(row)
    
    container_client = blob_service_client.get_container_client(container="csv-container")
    res = await container_client.upload_blob(name=filename, data=out_stream.getvalue(), overwrite=True)
    print("uploaded results back as: " + filename)
    
    blob_service_client.close()

    # TODO Send updated status/filename to backend
    update_job_succeeded(blob_name, filename)
    return func.HttpResponse(
        "File processed successfully",
        status_code=200
    )
