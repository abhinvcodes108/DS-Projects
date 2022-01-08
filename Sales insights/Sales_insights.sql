Select * FROM sales.transactions;

-- Converting USD values to INR

UPDATE sales.transactions SET sales_amount=sales_amount*74.31 WHERE sales.transactions.currency='USD';

UPDATE sales.transactions SET currency='INR' WHERE currency='USD';

SELECT * FROM sales.transactions WHERE currency='USD';



-- Top 10 of the lowest revenue markets

SELECT sum(sales_amount) AS total_revenue,market_code 
FROM sales.transactions GROUP BY market_code 
ORDER BY total_revenue asc 
LIMIT 10;



-- Top 10 of the Highest revenue markets

SELECT sum(sales_amount) AS total_revenue,market_code 
FROM sales.transactions 
GROUP BY market_code 
ORDER BY total_revenue desc 
LIMIT 10;



-- Total Revenue from Chennai in the year 2020

SELECT sales.transactions.*,sales.date.* ,SUM(sales.transactions.sales_amount) AS Revenue

FROM sales.transactions 

JOIN sales.date 

ON sales.transactions.order_date=sales.date.date

WHERE sales.date.year=2020 AND sales.transactions.market_code='Mark001';
