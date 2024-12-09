from flask import Flask, render_template, request, send_from_directory, redirect, url_for, send_file
import pandas as pd
import os
import time
import uuid

app = Flask(__name__)

# Ensure the static folder exists
if not os.path.exists('static'):
    os.makedirs('static')

# Route to handle file upload and select transformation
@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        transformation = request.form.get('transformation')
        
        # Save the file to a temporary location
        if file:
            filename = os.path.join('static', file.filename)
            file.save(filename)
            
            # Save transformation and form data
            app.config['uploaded_file'] = filename
            app.config['transformation'] = transformation
            app.config['filter_column'] = request.form.get('filter_column')
            app.config['filter_value'] = request.form.get('filter_value')
            app.config['sort_column'] = request.form.get('sort_column')
            app.config['fill_column'] = request.form.get('fill_column')
            app.config['fill_value'] = request.form.get('fill_value')
            app.config['rename_columns'] = request.form.get('rename_columns')
        
        return redirect(url_for('loading'))
    
    return render_template('upload.html')  # This page will allow file upload and transformation selection

# Route for loading page (simulating processing delay)
@app.route('/loading')
def loading():
    #return render_template('loading.html')
    time.sleep(2)  # Simulate processing delay

    # Retrieve the uploaded file and process the data
    filename = app.config.get('uploaded_file')
    transformation = app.config.get('transformation')
    filter_column = app.config.get('filter_column')
    filter_value = app.config.get('filter_value')
    sort_column = app.config.get('sort_column')
    fill_column = app.config.get('fill_column')
    fill_value = app.config.get('fill_value')
    rename_columns = app.config.get('rename_columns')

    if filename:
        # Read the uploaded file
        df = pd.read_excel(filename)

        # step 1: Perform the selected transformation
        if transformation == 'remove_duplicates':
            print(df.head())  # Display the first few rows for debugging
            print(f"Shape before: {df.shape}")  # Debugging: shape before dropping duplicates    
            # Drop duplicates based on all columns except 'Number'
            df.drop_duplicates(subset=[col for col in df.columns if col != 'Number'], inplace=True)   
            print(f"Shape after: {df.shape}")  # Debugging: shape after dropping duplicates
        elif transformation == 'change_column_names':
            df.rename(columns=lambda x: x.strip().lower().replace(" ", "_"), inplace=True)
        elif transformation == 'fill_missing_values':
            if fill_column and fill_value is not None:
                df[fill_column].fillna(value=fill_value, inplace=True)
            else:
                df.fillna(value=fill_value or 'N/A', inplace=True)
        elif transformation == 'filter_rows':
            if filter_column and filter_value:
                try:
                    filter_value_cast = pd.to_numeric(filter_value, errors='coerce') if filter_value.isnumeric() else filter_value
                    df = df[df[filter_column] == filter_value_cast]
                except KeyError:
                    return render_template('loading.html', error="Filter column not found in data.")
        elif transformation == 'sort_data':
            if sort_column:
                df.sort_values(by=sort_column, inplace=True)
            else:
                return render_template('loading.html', error="Sort column not specified.")

        # Save the processed file
        output_path = os.path.join('static', 'processed_file.xlsx')
        df.to_excel(output_path, index=False)

    return redirect(url_for('download'))  # Redirect to the download page after processing

# Route to download the processed file
@app.route('/download')
def download():
    return render_template('download.html', filename='processed_file.xlsx')

# Route for the download link to retrieve the file
@app.route('/download_file/<filename>')
def download_file(filename):
    return send_from_directory('static', filename, as_attachment=True)

#Route for listing split files for download
@app.route("/download_splits")
def download_splits():
    split_files = app.config.get('split_files', [])
    return render_template('download_splits.html', files=split_files)

if __name__ == '__main__':
    app.run(debug=True)
