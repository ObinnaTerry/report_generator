SELECT t2.taxpayer_code    AS 'TPIN',
       t2.taxpayer_name    AS 'Taxpayer Name',
       t2.device_code      AS 'Terminal ID',
       t2.taxpayer_address AS 'Taxpayer Address',
       t2.tax_office       AS 'Tax Office',
       t3.drawer_time      AS 'Last Time',
       (SELECT dict_name
        FROM   sys_dictionaries
        WHERE  dict_type = 'industry_code'
               AND dict_code = t2.industry_code) AS 'Sector'
FROM  (SELECT t.base_id,
              t.taxpayer_code,
              t.taxpayer_name,
              t1.device_code,
              t.taxpayer_address,
              t.industry_code,
              (SELECT depart_name
               FROM   sys_department
               WHERE  t.belong_tfcode = depart_code
                      AND ` status ` = '1') AS tax_office
       FROM   taxpayer_base_info t,
              (SELECT b.base_id,
                      b.device_code
               FROM   ims_device_info a,
                      ims_device_reginfo b
               WHERE  a.device_id = b.device_id
                      AND a .` status ` IN ( '2', '3', '4' )
                      AND b .` status ` = '2') t1
       WHERE  t.base_id = t1.base_id) t2
      left outer join (SELECT base_id,
                              device_code,
                              Max(drawer_time) drawer_time
                       FROM   invoice_issue
                       GROUP  BY device_code) t3
                   ON t2.device_code = t3.device_code
WHERE  drawer_time IS NULL
ORDER  BY t3.drawer_time,
          t2.device_code,
          t2.taxpayer_code,
          t2.tax_office
INTO OUTFILE '/var/lib/mysql-files/never_invoiced.csv' 
FIELDS ENCLOSED BY '"' 
TERMINATED BY ',' 
ESCAPED BY '"' 
LINES TERMINATED BY '\r\n';