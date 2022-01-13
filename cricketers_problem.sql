SELECT * FROM sys.cricketers;

-- Creating a table of leaders and their scores to compare with the scores of other players
WITH CTE AS(SELECT Name as Captain, Country,MAX(Runs) as Captain_runs FROM sys.cricketers GROUP BY Country )
SELECT * FROM sys.cricketers a JOIN CTE b ON a.Country=b.Country ;

-- Comparing the scores of players of each country with their leader's scores and counting the numbers

WITH CTE AS(SELECT Name as Captain, Country,MAX(Runs) as Captain_runs FROM sys.cricketers GROUP BY Country )
SELECT COUNT(Name),a.Country FROM sys.cricketers a JOIN CTE b ON a.Country=b.Country 
WHERE a.Runs>=(Captain_runs-500) AND a.Name<>b.Captain GROUP BY a.Country;