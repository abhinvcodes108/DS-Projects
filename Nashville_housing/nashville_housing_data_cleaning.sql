SELECT * FROM housing_prices.nv_housing;
DESCRIBE housing_prices.nv_housing;

-- Updating SaleDate to Datetime format
SELECT SaleDate FROM housing_prices.nv_housing;
UPDATE housing_prices.nv_housing SET SaleDate=str_to_date(SaleDate,'%M %d, %YT%H:%i:%s.%f');
UPDATE housing_prices.nv_housing SET SaleDate=DATE(SaleDate);

-- Populate Property Address
SELECT a.ParcelID,a.PropertyAddress,b.ParcelID,b.PropertyAddress,ISNULL(a.PropertyAddress,b.PropertyAddress) 
FROM housing_prices.nv_housing a
JOIN housing_prices.nv_housing b
ON a.ParcelID=b.ParcelID AND a.UniqueID<>b.UniqueID WHERE a.PropertyAddress=NULL;

UPDATE housing_prices.nv_housing a JOIN housing_prices.nv_housing b
ON a.ParcelID=b.ParcelID AND a.UniqueID<>b.UniqueID 
SET a.PropertyAddress=ISNULL(a.PropertyAddress,b.PropertyAddress)
WHERE a.PropertyAddress=NULL;

-- Breaking out Property Address into separate columns(Address,City,State)
SELECT PropertyAddress FROM housing_prices.nv_housing;
SELECT SUBSTRING(PropertyAddress,1,LOCATE(',',PropertyAddress)-1) as Address,
SUBSTRING(PropertyAddress,LOCATE(',',PropertyAddress)+1,LENGTH(PropertyAddress)) as City
FROM housing_prices.nv_housing;

ALTER TABLE housing_prices.nv_housing ADD COLUMN Property_Split_Address varchar(255);
UPDATE housing_prices.nv_housing SET Property_Split_Address=SUBSTRING(PropertyAddress,1,LOCATE(',',PropertyAddress)-1);
ALTER TABLE housing_prices.nv_housing ADD COLUMN Property_Split_City varchar(255);
UPDATE housing_prices.nv_housing 
SET Property_Split_City=SUBSTRING(PropertyAddress,LOCATE(',',PropertyAddress)+1,LENGTH(PropertyAddress));

-- Breaking out Owner Address into separate columns(Address,City,State)
SELECT SUBSTRING_INDEX(OwnerAddress,',',1) FROM housing_prices.nv_housing;
ALTER TABLE housing_prices.nv_housing ADD COLUMN Owner_Split_Address varchar(255);
UPDATE housing_prices.nv_housing SET Owner_Split_Address=SUBSTRING_INDEX(OwnerAddress,',',1);

ALTER TABLE housing_prices.nv_housing ADD COLUMN Owner_Split_City VARCHAR(255);
SELECT SUBSTRING((SUBSTRING_INDEX(OwnerAddress,',',-2)),1,LOCATE(',',SUBSTRING_INDEX(OwnerAddress,',',-2))-1) FROM housing_prices.nv_housing;
UPDATE housing_prices.nv_housing 
SET Owner_Split_City=SUBSTRING((SUBSTRING_INDEX(OwnerAddress,',',-2)),1,LOCATE(',',SUBSTRING_INDEX(OwnerAddress,',',-2))-1);

ALTER TABLE housing_prices.nv_housing ADD COLUMN Owner_Split_State VARCHAR(255);
UPDATE housing_prices.nv_housing SET Owner_Split_State=SUBSTRING_INDEX(OwnerAddress,',',-1);

-- Change Y and N to Yes and No in Sold As Vacant
SELECT DISTINCT(SoldAsVacant) FROM housing_prices.nv_housing;
UPDATE housing_prices.nv_housing SET SoldAsVacant='No' WHERE SoldAsVacant='N';

-- Remove Duplicates
WITH RowNumCTE AS (
SELECT *,
	ROW_NUMBER() OVER (
    PARTITION BY ParcelID,
				 PropertyAddress,
                 SaleDate,
                 SalePrice,
                 LegalReference
                 ORDER BY
					UniqueID) row_num
FROM housing_prices.nv_housing)
SELECT * FROM RowNumCTE WHERE row_num>1;
 
	


















