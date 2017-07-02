# HooperHub
Try it out at [hooperhub.io](http://hooperhub.io)!
<img src="screenshot.jpg" />
### Requirements
- python >3.5
- python3-pip
- virtualenv (optional)
- A POSIX compliant environment is preferred
### Downloading
Clone and cd into the project directory
```
$ git clone https://github.com/jay-smoove/HooperHub
$ cd HooperHub
```
Export ```HH_ROOT``` as the project directory root
```
$ export HH_ROOT=$PWD
```
Install requirements (use a virtualenv if preferred)
```
$ pip install -r requirements.txt # or requirements-gpu.txt
```
### Training
All commands are being executed from ```$HH_ROOT```. Training may take time depending on your hardware specs.
> NUM_EXAMPLES: The number of training example pairs to produce (at least 1000000 should suffice)
```
$ python tools/synthetic_data/generate_data.py --num_examples={NUM_EXAMPLES} > hooperhub/data/training.tsv
$ python hooperhub/bin/train.py --data_dir=hooperhub/data/
```
### Running the demo
After training, let's run the demo! 
```
$ python run_me.py
```
Note: The demo won't give any actual results since that requires access to the database. Instead, the demo produces the information that it would query to the database if there was one. For a demo that actually calculates statistics visit [hooperhub.io](http://hooperhub.io)!