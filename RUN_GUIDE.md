# Run Guide (Mac)

1. Open Terminal, go to the project folder:  `cd ~/olist-project`
2. Create the environment (first time only):
   `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
   (Next time, only `source venv/bin/activate`.)
3. Download the dataset from Kaggle and put all .csv files in `data/raw/`.
4. Run, in this order, from the project folder:
   - `python python/clean_data.py`    -> prints the data-quality report
   - `python python/build_db.py`      -> creates olist.db
   - `python python/run_queries.py`   -> prints 8 results, saves them in outputs/
   - `streamlit run python/app.py`    -> opens the dashboard in your browser
5. Take a screenshot of the dashboard, save as `screenshots/dashboard.png`.
6. Fill every [ ] in README.md using your real outputs.
