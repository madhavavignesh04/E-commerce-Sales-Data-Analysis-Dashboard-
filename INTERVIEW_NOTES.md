# Interview Notes (for you, not for GitHub)

## 30-second pitch
"I analysed about [N] real e-commerce orders from Olist, a Brazilian marketplace. I cleaned seven tables with Pandas, loaded them into SQLite, answered eight business questions with SQL, and built a Streamlit dashboard. The main finding was [your best finding with a number]."

## Questions you WILL be asked (answer from your own results)
1. **Why did you exclude non-delivered orders?** Revenue should reflect completed sales; canceled or in-transit orders would inflate it.
2. **Why customer_unique_id and not customer_id?** customer_id is generated per order, so using it would show 0% repeat customers.
3. **Why keep only the latest review per order?** Some orders have several reviews; counting all would double-count orders.
4. **Explain a window function you used.** Open `sql/analysis.sql`, take q1 (LAG) or q8 (RANK with PARTITION BY) and walk through it line by line.
5. **Why a CTE instead of a subquery?** Readability: each step has a name and can be read top to bottom.
6. **Why SQLite?** Zero setup, same SQL for these queries; I would move to MySQL/PostgreSQL for multi-user or larger data. 
7. **What would you do next?** Customer segmentation, seller performance, forecasting monthly revenue.
8. **What are the limitations?** Old data, no cost/profit data, correlation is not causation.

## Be ready to
- Open the dashboard live and change a filter, then say what changed and why.
- Explain every number on your README (where it came from: which query or report line).
- Say honestly what you learned and what was hard.
