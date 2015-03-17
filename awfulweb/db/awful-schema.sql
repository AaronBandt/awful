use awful;

###
### TABLE: users
###   This is the local users table for installs that do not
###   wish to use AD/LDAP
###
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `user_id`                mediumint(9) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `user_name`              varchar(250) COLLATE utf8_bin NOT NULL,
  `first_name`             varchar(250) COLLATE utf8_bin,
  `last_name`              varchar(250) COLLATE utf8_bin,
  `salt`                   varchar(50) COLLATE utf8_bin NOT NULL,
  `password`               varchar(250) COLLATE utf8_bin NOT NULL,
  `updated_by`             varchar(200) COLLATE utf8_bin NOT NULL,
  `created`                timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated`                timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE UNIQUE INDEX idx_user_name_unique on users (user_name);

###
### TABLE: user_group_assignments
###   This table assigns local users to groups.
###
DROP TABLE IF EXISTS `user_group_assignments`;
CREATE TABLE `user_group_assignments` (
  `user_group_assignment_id`    mediumint(9) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `group_id`                    mediumint(9) UNSIGNED NOT NULL,
  `user_id`                     mediumint(9) UNSIGNED NOT NULL,
  `updated_by`                  varchar(200) COLLATE utf8_bin NOT NULL,
  `created`                     timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated`                     timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

###
### TABLE: groups
###   This is the primary groups table.
###
DROP TABLE IF EXISTS `groups`;
CREATE TABLE `groups` (
  `group_id`               mediumint(9) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `group_name`             varchar(250) COLLATE utf8_bin NOT NULL,
  `updated_by`             varchar(200) COLLATE utf8_bin NOT NULL,
  `created`                timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated`                timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE UNIQUE INDEX idx_group_name_unique on groups (group_name);

###
### TABLE: places
###   AWFUL places to eat
###
DROP TABLE IF EXISTS `places`;
CREATE TABLE `places` (
  `place_id`           mediumint(9) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name`               varchar(250) COLLATE utf8_bin NOT NULL,
  `updated_by`         varchar(30) NOT NULL,
  `created`            timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated`            timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE UNIQUE INDEX idx_places_unique on places (name);

###
### TABLE: ratings
###   How AWFUL is it? 
###
DROP TABLE IF EXISTS `ratings`;
CREATE TABLE `ratings` (
  `rating_id`          mediumint(9) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `place_id`           mediumint(9) UNSIGNED NOT NULL,
  `rating`             mediumint(9) UNSIGNED NOT NULL,
  `updated_by`         varchar(30) NOT NULL,
  `created`            timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated`            timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE UNIQUE INDEX idx_ratings_unique on ratings (place_id, updated_by);


