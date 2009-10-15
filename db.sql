DROP TABLE IF EXISTS apartments;
DROP TABLE IF EXISTS area;
DROP TABLE IF EXISTS region;
DROP TABLE IF EXISTS metrics;

CREATE TABLE `metrics` (
  `id` int(11) unsigned NOT NULL auto_increment,
  `key` varchar(40) default NULL,
  `value` int(11) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `region` (
  `id` int(10) unsigned NOT NULL auto_increment,
  `name` varchar(40) NOT NULL default 'UNKNOWN',
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `area` (
  `id` int(10) unsigned NOT NULL auto_increment,
  `region_id` int(10) unsigned NOT NULL,
  `name` varchar(40) NOT NULL default 'UNKNOWN',
  PRIMARY KEY  (`id`),
  KEY `region_id` (`region_id`),
  CONSTRAINT `area_ibfk_1` FOREIGN KEY (`region_id`) REFERENCES `region` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `apartments` (
  `id` int(10) unsigned NOT NULL auto_increment,
  `cl_id` varchar(11) NOT NULL,
  `area_id` int(10) unsigned NOT NULL,
  `posted_date` datetime default NULL,
  `email` varchar(40) default NULL,
  `phone` varchar(12) default NULL,
  `price` int(10) unsigned NOT NULL default '0',
  `bedrooms` smallint(5) unsigned NOT NULL default '0',
  `bathrooms` smallint(5) unsigned default NULL,
  `title` varchar(128) NOT NULL default '',
  `body` text NOT NULL,
  `is_open_house` tinyint(4) NOT NULL default '0',
  `location` varchar(128) NOT NULL default '',
  `latitude` float(23,8) NOT NULL default '0.00000000',
  `longitude` float(23,8) NOT NULL default '0.00000000',
  `url` varchar(128) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

INSERT INTO region (id, name) VALUES (NULL, 'sfbay');

