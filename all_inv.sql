SET @date_limit : = ;
SET @target_year_month : = ;

SELECT t2.taxpayer_code    AS 'TPIN',
       t2.taxpayer_name    AS 'Taxpayer Name',
       t2.device_code      AS 'Terminal ID',
       t2.taxpayer_address AS 'Taxpayer Address',
       t2.tax_office       AS 'Tax Office',
       t3.drawer_time      AS 'Latest Time',
       t3.issued,
       t3.total_sales,
       t3.total_tax,
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
                      AND b .` status ` = '2') t1
       WHERE  t.base_id = t1.base_id) t2
      RIGHT OUTER JOIN (SELECT z.base_id,
                               Count(z.base_id)   'issued',
                               z.device_code,
                               Max(z.drawer_time) drawer_time,
                               SUM(z.total_sales) 'total_sales',
                               SUM(z.total_tax)   'total_tax'
                        FROM   (SELECT base_id,
                                       device_code,
                                       base_id                      AS 'issued',
                                       amount * conversion_rate     AS
                                       'total_sales',
                                       tax_amount * conversion_rate AS
                                       'total_tax',
                                       drawer_time                  drawer_time
                                FROM   invoice_issue
                                WHERE  drawer_time < @date_limit) z
                        GROUP  BY z.device_code) t3
                    ON t2.device_code = t3.device_code
ORDER  BY t3.drawer_time,
          t2.device_code,
          t2.taxpayer_code,
          t2.tax_office;