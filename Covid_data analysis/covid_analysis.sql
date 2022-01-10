select * from covid_project..covid_de

select location,date,new_cases,total_cases,total_deaths
from covid_project..covid_de
order by 3,2

---Comparing total cases and total deaths
select location,date,total_cases,total_deaths,(total_deaths/total_cases)*100
from covid_project..covid_de
where location like '%India'
order by 1,2;

---Comparing total cases vs population- Countries with the highest infection rates
select location,population,MAX(total_cases) as HighestInfectionCounts,
(max(total_cases)/population)*100 as 'Afflicted Percentage Population'
from covid_project..covid_de
GROUP BY location,population
order by 'Afflicted Percentage Population' DESC;

---Countries with highest death count
select location,MAX(cast(total_deaths as bigint)) as HighestDeathCounts
from covid_project..covid_de
where continent is not null
GROUP BY location
order by HighestDeathCounts DESC;

---Continents with highest death count
select location,MAX(cast(total_deaths as bigint)) as HighestDeathCounts
from covid_project..covid_de
where continent is null
GROUP BY location
order by HighestDeathCounts DESC;

---Global numbers
select date,sum(new_cases) as total_cases,sum(cast(new_deaths as int)) as total_deaths,
(sum(cast(new_deaths as int))/sum(new_cases))*100 as 'deaths_percentage'
from covid_project..covid_de
where continent is not null
GROUP BY date
order by 1,2;

select sum(new_cases) as total_cases,sum(cast(new_deaths as int)) as total_deaths,
(sum(cast(new_deaths as int))/sum(new_cases))*100 as 'deaths_percentage'
from covid_project..covid_de
where continent is not null
order by 1,2;

---Total population vs vaccinations
select dea.location,dea.population,dea.date,vcc.new_vaccinations,
sum(cast(vcc.new_vaccinations as bigint)) over (partition by dea.location Order By dea.date) as RollingPeopleVaccinated
from covid_project..covid_de as dea
join covid_project..covid_vccn as vcc
on dea.location=vcc.location
 and  dea.date=vcc.date
where dea.continent is not null
order by 1,3;

---Using CTE
With popvsvac(Continent,Location,Population,Date,New_Vaccinations,RollingPeopleVaccinated)
as(
select dea.continent,dea.location,dea.population,dea.date,vcc.new_vaccinations,
sum(cast(vcc.new_vaccinations as bigint)) over (partition by dea.location Order By dea.date) as RollingPeopleVaccinated
from covid_project..covid_de as dea
join covid_project..covid_vccn as vcc
on dea.location=vcc.location
 and  dea.date=vcc.date
---where dea.continent is not null
--order by 1,3
)
select *,(RollingPeopleVaccinated/Population)*100 as total_death_percentage
from popvsvac;






---Temp Table


Drop Table if exists #percentage_population_vaccinated
Create Table #percentage_population_vaccinated
(
Continent nvarchar(255),
Location nvarchar(255),
Population numeric,
Date datetime,
new_vaccinations numeric,
RollingPeopleVaccinated numeric
)

Insert into #percentage_population_vaccinated
select dea.continent,dea.location,dea.population,dea.date,vcc.new_vaccinations,
sum(cast(vcc.new_vaccinations as bigint)) over (partition by dea.location Order By dea.date) as RollingPeopleVaccinated
from covid_project..covid_de as dea
join covid_project..covid_vccn as vcc
on dea.location=vcc.location
 and  dea.date=vcc.date
---where dea.continent is not null
--order by 1,3

select *,(RollingPeopleVaccinated/Population)*100 as total_death_percentage
from #percentage_population_vaccinated

---Creating a view to store data for later visualisation
create view PercentagePopulationVaccinated as
select dea.continent,dea.location,dea.population,dea.date,vcc.new_vaccinations,
sum(cast(vcc.new_vaccinations as bigint)) over (partition by dea.location Order By dea.date) as RollingPeopleVaccinated
from covid_project..covid_de as dea
join covid_project..covid_vccn as vcc
on dea.location=vcc.location
 and  dea.date=vcc.date
where dea.continent is not null
--order by 1,3

select * from PercentagePopulationVaccinated