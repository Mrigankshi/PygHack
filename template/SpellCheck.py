import pandas as pd
import numpy as np
import sys 
from google.cloud import bigquery
import time
import os
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename


#Make connection to bigquery
try:
    client = bigquery.Client.from_service_account_json('/data/shreshtha/service_account.json')
    print('Info: Connected to BigQuery database\n')
except Exception as e:
    print(e)

def run_query(d,l):

	global path

	query = """--SearchTaps keyword from
	Select d.keyword,d.search_tap,  (length(d.keyword)- length(replace(d.keyword, " ", "")) + 1) as tokens
	from
	(select
	keyword,
	sum(ft) as first_tap,sum(st) as search_tap
	from
	(
	select r.device_id as device_id, r.session_id as session_id, r.attempt_id as attempt_id,keyword,sum(first_tap) as ft,sum(search_tap) as st
	from
	(
	select p.device_id as device_id, p.session_id as session_id,p.attempt_id as attempt_id,keyword,
	sum(case when action_type in ('3') then 1 else 0 end) as first_tap,
	-- sum(case when action_type_id in ('12') and action_detail_id in ('13') then 1 else 0 end) as search_tap
	count(*) as search_tap
	from
	(
	select x.device_id as device_id, x.session_id as session_id,x.attempt_id as attempt_id,keyword,action_type_id,action_detail_id
	from
	(
	select device_id,session_id,attempt_id
	from `gaana-bigquery-1315.gaana_search_logs_hive.tm_search_event_client_*`
	where _table_suffix between '""" + str(d) + """' and '"""  + str(d) + """' and platform in ('5') and app_version IN ('gaanaAndroid-8.2.0','gaanaAndroid-8.3.0','gaanaAndroid-8.3.1','gaanaAndroid-8.3.2','gaanaAndroid-8.4.0','gaanaAndroid-8.4.1','gaanaAndroid-8.4.2','gaanaAndroid-8.4.3','gaanaAndroid-8.4.4','gaanaAndroid-8.5.0','gaanaAndroid-8.5.1','gaanaAndroid-8.5.2','gaanaAndroid-8.5.3','gaanaAndroid-8.5.4','gaanaAndroid-8.6.0','gaanaAndroid-8.6.1','gaanaAndroid-8.6.2','gaanaAndroid-8.6.3','gaanaAndroid-8.6.4','gaanaAndroid-8.6.5','gaanaAndroid-8.6.6','gaanaAndroid-8.6.7','gaanaAndroid-8.6.8','gaanaAndroid-8.6.9','gaanaAndroid-8.7.0') and action_type_id in ('2') and action_detail_id in ('0')
	group by 1,2,3
	)x
	join
	(
	select format_datetime("%Y-%m-%d",cast (created_at as datetime)) as created_at, action_type_id,action_detail_id,device_id,session_id,attempt_id,search_id,app_version,replace(replace(lower(ltrim(rtrim(keyword))),'.',''),'(','') as keyword
	from `gaana-bigquery-1315.gaana_search_logs_hive.tm_search_event_client_*`
	where _table_suffix between '""" + str(d) + """' and '""" + str(d) + """' and platform in ('5') and app_version IN ('gaanaAndroid-8.2.0','gaanaAndroid-8.3.0','gaanaAndroid-8.3.1','gaanaAndroid-8.3.2','gaanaAndroid-8.4.0','gaanaAndroid-8.4.1','gaanaAndroid-8.4.2','gaanaAndroid-8.4.3','gaanaAndroid-8.4.4','gaanaAndroid-8.5.0','gaanaAndroid-8.5.1','gaanaAndroid-8.5.2','gaanaAndroid-8.5.3','gaanaAndroid-8.5.4','gaanaAndroid-8.6.0','gaanaAndroid-8.6.1','gaanaAndroid-8.6.2','gaanaAndroid-8.6.3','gaanaAndroid-8.6.4','gaanaAndroid-8.6.5','gaanaAndroid-8.6.6','gaanaAndroid-8.6.7','gaanaAndroid-8.6.8','gaanaAndroid-8.6.9','gaanaAndroid-8.7.0') and action_type_id in ('12')
	group by 1,2,3,4,5,6,7,8,9
	)y
	on x.device_id=y.device_id and x.session_id=y.session_id and x.attempt_id=y.attempt_id
	)p
	left join
	(
	select device_id,session_id,attempt_id,action_type_id as action_type,action_detail_id as action_detail
	from `gaana-bigquery-1315.gaana_search_logs_hive.tm_search_event_client_*`
	where _table_suffix between '"""  + str(d) + """' and '""" + str(d) + """' and platform in ('5') and app_version IN ('gaanaAndroid-8.2.0','gaanaAndroid-8.3.0','gaanaAndroid-8.3.1','gaanaAndroid-8.3.2','gaanaAndroid-8.4.0','gaanaAndroid-8.4.1','gaanaAndroid-8.4.2','gaanaAndroid-8.4.3','gaanaAndroid-8.4.4','gaanaAndroid-8.5.0','gaanaAndroid-8.5.1','gaanaAndroid-8.5.2','gaanaAndroid-8.5.3','gaanaAndroid-8.5.4','gaanaAndroid-8.6.0','gaanaAndroid-8.6.1','gaanaAndroid-8.6.2','gaanaAndroid-8.6.3','gaanaAndroid-8.6.4','gaanaAndroid-8.6.5','gaanaAndroid-8.6.6','gaanaAndroid-8.6.7','gaanaAndroid-8.6.8','gaanaAndroid-8.6.9','gaanaAndroid-8.7.0') and action_type_id in ('3')
	group by 1,2,3,4,5
	)i
	on p.device_id=i.device_id and p.session_id=i.session_id and p.attempt_id=i.attempt_id
	where (length(keyword)- length(replace(keyword, " ", "")) + 1)>3
	group by 1,2,3,4
	)r

	group by 1,2,3,4
	)u
	group by 1)d

	group by 1,2,tokens
	order by d.search_tap desc"""

	print("Info: Query Running")

	df = pd.read_gbq(query, project_id='gaana-bigquery-1315', private_key='/data/shreshtha/service_account.json', dialect='standard')
	df = df[df['tokens'] == l]

	path = "/data/shreshtha/raw_data/" + str(d) + "_len" + str(l) + ".csv"

	df.to_csv(path)


# df = pd.DataFrame()
# df = run_query(query)

# print(df)
# exit()

#Define query

# print(query)
# exit()


UPLOAD_FOLDER = '/data/shreshtha/processed_data/'
ALLOWED_EXTENSIONS = {'csv'}


app = Flask(__name__,template_folder='/data/shreshtha/')
app.secret_key = "secret"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/', methods=['POST'])
def get_args():
    global date, token
    date = request.form['date']
    length = int(request.form['length'])
    run_query(date,length)
  
    return render_template('download.html')


@app.route('/download')
def download_file():
    # path = r"/data/shreshtha/raw_data/temp.csv"
    return send_file(path, as_attachment = True)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET','POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('upload_file',filename=filename))
    
    return render_template('upload.html')


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port = 80, host = '172.26.61.200')

