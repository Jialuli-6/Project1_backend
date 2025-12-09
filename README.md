This repo includes backend documents.</br>


<h2>Environment Requirements</h2>

<h3>Basic Dependencies</h3>
• Operating System: Windows/macOS/Linux•Python 3.8+</br>
• Node.js 14.x+ and npm 6.x+</br>
• Network Environment: Local service ports must be accessible</br>

<h3>Required Software</h3>
• Git (optional, for code cloning)</br>
• Web Browser (Chrome/Firefox latest versions recommended)</br>


<h2>Data Requirements</h2>

```python
├─/root/Project Folder
        ├─node_modules
        ├─public
        ├─src
             ├─components
                    ├─ .tsx files 
             ├─data 
             ├─backend (App.py)
             ├─venv
...
```



<h2>Backend Application Deployment</h2>


<h3>Obtain Backend Code</h3>
Copy the backend code directory containing app.py to the target server:</br>

```python
cd backend  # Navigate to backend code directory
```

<h3>Install Dependencies</h3>

```python
# Create virtual environment
python -m venv venv
# macOS/Linux
source venv/bin/activate
```

<h4>Example from MacOS</h4>

```python
cd ../Desktop/../yeshiva-network/src
python -m venv venv
source venv/bin/activate
```

<h4>Install required packages:</h4>

```python
pip install flask flask-cors pandas numpy
```

<h3>Start Backend Environment</h3>

```python
python app.py
```

The service will run at http://0.0.0.0:5000. </br>
Verify startup by accessing http://localhost:5000/api/paper-counts.


