/*M!999999\- enable the sandbox mode */ 

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `lycee_ambohitromby` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;

USE `lycee_ambohitromby`;
DROP TABLE IF EXISTS `absence`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `absence` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `statut` varchar(10) NOT NULL,
  `heures_absence` decimal(4,2) NOT NULL,
  `motif` varchar(255) NOT NULL,
  `observation` varchar(255) NOT NULL,
  `inscription_id` bigint(20) NOT NULL,
  `appel_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_absence` (`appel_id`,`inscription_id`),
  KEY `absence_inscription_id_40f88791_fk_inscription_id` (`inscription_id`),
  CONSTRAINT `absence_appel_id_efdf87b8_fk_appel_id` FOREIGN KEY (`appel_id`) REFERENCES `appel` (`id`),
  CONSTRAINT `absence_inscription_id_40f88791_fk_inscription_id` FOREIGN KEY (`inscription_id`) REFERENCES `inscription` (`id`),
  CONSTRAINT `chk_heures` CHECK (`heures_absence` >= 0)
) ENGINE=InnoDB AUTO_INCREMENT=787 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `absence` WRITE;
/*!40000 ALTER TABLE `absence` DISABLE KEYS */;
/*!40000 ALTER TABLE `absence` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `annee_scolaire`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `annee_scolaire` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `annee_debut` smallint(5) unsigned NOT NULL CHECK (`annee_debut` >= 0),
  `annee_fin` smallint(5) unsigned NOT NULL CHECK (`annee_fin` >= 0),
  `libelle` varchar(15) NOT NULL,
  `courante` tinyint(1) NOT NULL,
  `classes_initialisees` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `annee_debut` (`annee_debut`),
  CONSTRAINT `chk_annee_bornes` CHECK (`annee_debut` >= 2020 and `annee_debut` <= 2045)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `annee_scolaire` WRITE;
/*!40000 ALTER TABLE `annee_scolaire` DISABLE KEYS */;
INSERT INTO `annee_scolaire` VALUES
(1,2020,2021,'2020 - 2021',0,0),
(2,2021,2022,'2021 - 2022',0,0),
(3,2022,2023,'2022 - 2023',0,0),
(4,2023,2024,'2023 - 2024',0,0),
(5,2024,2025,'2024 - 2025',0,0),
(6,2025,2026,'2025 - 2026',0,0),
(7,2026,2027,'2026 - 2027',1,1),
(8,2027,2028,'2027 - 2028',0,0),
(9,2028,2029,'2028 - 2029',0,0),
(10,2029,2030,'2029 - 2030',0,0),
(11,2030,2031,'2030 - 2031',0,0),
(12,2031,2032,'2031 - 2032',0,0),
(13,2032,2033,'2032 - 2033',0,0),
(14,2033,2034,'2033 - 2034',0,0),
(15,2034,2035,'2034 - 2035',0,0),
(16,2035,2036,'2035 - 2036',0,0),
(17,2036,2037,'2036 - 2037',0,0),
(18,2037,2038,'2037 - 2038',0,0),
(19,2038,2039,'2038 - 2039',0,0),
(20,2039,2040,'2039 - 2040',0,0),
(21,2040,2041,'2040 - 2041',0,0),
(22,2041,2042,'2041 - 2042',0,0),
(23,2042,2043,'2042 - 2043',0,0),
(24,2043,2044,'2043 - 2044',0,0),
(25,2044,2045,'2044 - 2045',0,0),
(26,2045,2046,'2045 - 2046',0,0);
/*!40000 ALTER TABLE `annee_scolaire` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `appel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `appel` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `duree_heures` decimal(4,2) NOT NULL,
  `date_saisie` datetime(6) NOT NULL,
  `classe_id` bigint(20) NOT NULL,
  `cours_id` bigint(20) DEFAULT NULL,
  `matiere_id` bigint(20) NOT NULL,
  `saisi_par_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_appel` (`matiere_id`,`date`,`cours_id`),
  KEY `appel_classe__99000d_idx` (`classe_id`,`date`),
  KEY `appel_cours_id_4d593227_fk_cours_id` (`cours_id`),
  KEY `appel_saisi_par_id_5aee72e6_fk_utilisateur_id` (`saisi_par_id`),
  CONSTRAINT `appel_classe_id_d9504367_fk_classe_id` FOREIGN KEY (`classe_id`) REFERENCES `classe` (`id`),
  CONSTRAINT `appel_cours_id_4d593227_fk_cours_id` FOREIGN KEY (`cours_id`) REFERENCES `cours` (`id`),
  CONSTRAINT `appel_matiere_id_a3e8722c_fk_matiere_id` FOREIGN KEY (`matiere_id`) REFERENCES `matiere` (`id`),
  CONSTRAINT `appel_saisi_par_id_5aee72e6_fk_utilisateur_id` FOREIGN KEY (`saisi_par_id`) REFERENCES `utilisateur` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=139 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `appel` WRITE;
/*!40000 ALTER TABLE `appel` DISABLE KEYS */;
/*!40000 ALTER TABLE `appel` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=101 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES
(1,'Can add content type',1,'add_contenttype'),
(2,'Can change content type',1,'change_contenttype'),
(3,'Can delete content type',1,'delete_contenttype'),
(4,'Can view content type',1,'view_contenttype'),
(5,'Can add permission',2,'add_permission'),
(6,'Can change permission',2,'change_permission'),
(7,'Can delete permission',2,'delete_permission'),
(8,'Can view permission',2,'view_permission'),
(9,'Can add group',3,'add_group'),
(10,'Can change group',3,'change_group'),
(11,'Can delete group',3,'delete_group'),
(12,'Can view group',3,'view_group'),
(13,'Can add Blacklisted Token',4,'add_blacklistedtoken'),
(14,'Can change Blacklisted Token',4,'change_blacklistedtoken'),
(15,'Can delete Blacklisted Token',4,'delete_blacklistedtoken'),
(16,'Can view Blacklisted Token',4,'view_blacklistedtoken'),
(17,'Can add Outstanding Token',5,'add_outstandingtoken'),
(18,'Can change Outstanding Token',5,'change_outstandingtoken'),
(19,'Can delete Outstanding Token',5,'delete_outstandingtoken'),
(20,'Can view Outstanding Token',5,'view_outstandingtoken'),
(21,'Can add discipline',6,'add_discipline'),
(22,'Can change discipline',6,'change_discipline'),
(23,'Can delete discipline',6,'delete_discipline'),
(24,'Can view discipline',6,'view_discipline'),
(25,'Can add etablissement',7,'add_etablissement'),
(26,'Can change etablissement',7,'change_etablissement'),
(27,'Can delete etablissement',7,'delete_etablissement'),
(28,'Can view etablissement',7,'view_etablissement'),
(29,'Can add utilisateur',8,'add_utilisateur'),
(30,'Can change utilisateur',8,'change_utilisateur'),
(31,'Can delete utilisateur',8,'delete_utilisateur'),
(32,'Can view utilisateur',8,'view_utilisateur'),
(33,'Can add donnee demo',9,'add_donneedemo'),
(34,'Can change donnee demo',9,'change_donneedemo'),
(35,'Can delete donnee demo',9,'delete_donneedemo'),
(36,'Can view donnee demo',9,'view_donneedemo'),
(37,'Can add journal audit',10,'add_journalaudit'),
(38,'Can change journal audit',10,'change_journalaudit'),
(39,'Can delete journal audit',10,'delete_journalaudit'),
(40,'Can view journal audit',10,'view_journalaudit'),
(41,'Can add professeur',11,'add_professeur'),
(42,'Can change professeur',11,'change_professeur'),
(43,'Can delete professeur',11,'delete_professeur'),
(44,'Can view professeur',11,'view_professeur'),
(45,'Can add famille',12,'add_famille'),
(46,'Can change famille',12,'change_famille'),
(47,'Can delete famille',12,'delete_famille'),
(48,'Can view famille',12,'view_famille'),
(49,'Can add annee scolaire',13,'add_anneescolaire'),
(50,'Can change annee scolaire',13,'change_anneescolaire'),
(51,'Can delete annee scolaire',13,'delete_anneescolaire'),
(52,'Can view annee scolaire',13,'view_anneescolaire'),
(53,'Can add classe',14,'add_classe'),
(54,'Can change classe',14,'change_classe'),
(55,'Can delete classe',14,'delete_classe'),
(56,'Can view classe',14,'view_classe'),
(57,'Can add eleve',15,'add_eleve'),
(58,'Can change eleve',15,'change_eleve'),
(59,'Can delete eleve',15,'delete_eleve'),
(60,'Can view eleve',15,'view_eleve'),
(61,'Can add inscription',16,'add_inscription'),
(62,'Can change inscription',16,'change_inscription'),
(63,'Can delete inscription',16,'delete_inscription'),
(64,'Can view inscription',16,'view_inscription'),
(65,'Can add matiere',17,'add_matiere'),
(66,'Can change matiere',17,'change_matiere'),
(67,'Can delete matiere',17,'delete_matiere'),
(68,'Can view matiere',17,'view_matiere'),
(69,'Can add cours',18,'add_cours'),
(70,'Can change cours',18,'change_cours'),
(71,'Can delete cours',18,'delete_cours'),
(72,'Can view cours',18,'view_cours'),
(73,'Can add paiement',19,'add_paiement'),
(74,'Can change paiement',19,'change_paiement'),
(75,'Can delete paiement',19,'delete_paiement'),
(76,'Can view paiement',19,'view_paiement'),
(77,'Can add trimestre',20,'add_trimestre'),
(78,'Can change trimestre',20,'change_trimestre'),
(79,'Can delete trimestre',20,'delete_trimestre'),
(80,'Can view trimestre',20,'view_trimestre'),
(81,'Can add decision conseil',21,'add_decisionconseil'),
(82,'Can change decision conseil',21,'change_decisionconseil'),
(83,'Can delete decision conseil',21,'delete_decisionconseil'),
(84,'Can view decision conseil',21,'view_decisionconseil'),
(85,'Can add note',22,'add_note'),
(86,'Can change note',22,'change_note'),
(87,'Can delete note',22,'delete_note'),
(88,'Can view note',22,'view_note'),
(89,'Can add resultat trimestre',23,'add_resultattrimestre'),
(90,'Can change resultat trimestre',23,'change_resultattrimestre'),
(91,'Can delete resultat trimestre',23,'delete_resultattrimestre'),
(92,'Can view resultat trimestre',23,'view_resultattrimestre'),
(93,'Can add appel',24,'add_appel'),
(94,'Can change appel',24,'change_appel'),
(95,'Can delete appel',24,'delete_appel'),
(96,'Can view appel',24,'view_appel'),
(97,'Can add absence',25,'add_absence'),
(98,'Can change absence',25,'change_absence'),
(99,'Can delete absence',25,'delete_absence'),
(100,'Can view absence',25,'view_absence');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `classe`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `classe` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `nom` varchar(50) NOT NULL,
  `droit_inscription` int(10) unsigned NOT NULL CHECK (`droit_inscription` >= 0),
  `caisse_soutien` int(10) unsigned NOT NULL CHECK (`caisse_soutien` >= 0),
  `annee_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_classe_annee_nom` (`annee_id`,`nom`),
  CONSTRAINT `classe_annee_id_62972197_fk_annee_scolaire_id` FOREIGN KEY (`annee_id`) REFERENCES `annee_scolaire` (`id`),
  CONSTRAINT `chk_classe_montants` CHECK (`caisse_soutien` <= 10000000 and `droit_inscription` <= 10000000)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `classe` WRITE;
/*!40000 ALTER TABLE `classe` DISABLE KEYS */;
INSERT INTO `classe` VALUES
(1,'Seconde',50000,0,7),
(2,'1ère L',60000,0,7),
(3,'1ère S',60000,0,7),
(4,'1ère OSE',60000,0,7),
(5,'Terminale L',70000,0,7),
(6,'Terminale S',70000,0,7),
(7,'Terminale OSE',70000,0,7);
/*!40000 ALTER TABLE `classe` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `cours`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `cours` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `jour` smallint(5) unsigned NOT NULL CHECK (`jour` >= 0),
  `heure_debut` time(6) NOT NULL,
  `heure_fin` time(6) NOT NULL,
  `salle` varchar(30) NOT NULL,
  `matiere_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `cours_matiere_8dc28c_idx` (`matiere_id`,`jour`),
  CONSTRAINT `cours_matiere_id_9bab9295_fk_matiere_id` FOREIGN KEY (`matiere_id`) REFERENCES `matiere` (`id`),
  CONSTRAINT `chk_cours_horaire` CHECK (`heure_debut` >= '07:00:00.000000' and `heure_debut` < `heure_fin` and `heure_fin` <= '18:00:00.000000' and `jour` >= 1 and `jour` <= 5)
) ENGINE=InnoDB AUTO_INCREMENT=43 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `cours` WRITE;
/*!40000 ALTER TABLE `cours` DISABLE KEYS */;
/*!40000 ALTER TABLE `cours` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `decision_conseil`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `decision_conseil` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `texte` varchar(255) NOT NULL,
  `inscription_id` bigint(20) NOT NULL,
  `trimestre_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_decision` (`inscription_id`,`trimestre_id`),
  KEY `decision_conseil_trimestre_id_049c3d0c_fk_trimestre_id` (`trimestre_id`),
  CONSTRAINT `decision_conseil_inscription_id_274e34b1_fk_inscription_id` FOREIGN KEY (`inscription_id`) REFERENCES `inscription` (`id`),
  CONSTRAINT `decision_conseil_trimestre_id_049c3d0c_fk_trimestre_id` FOREIGN KEY (`trimestre_id`) REFERENCES `trimestre` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `decision_conseil` WRITE;
/*!40000 ALTER TABLE `decision_conseil` DISABLE KEYS */;
/*!40000 ALTER TABLE `decision_conseil` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `discipline`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `discipline` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nom` (`nom`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `discipline` WRITE;
/*!40000 ALTER TABLE `discipline` DISABLE KEYS */;
/*!40000 ALTER TABLE `discipline` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES
(25,'absences','absence'),
(24,'absences','appel'),
(3,'auth','group'),
(2,'auth','permission'),
(6,'comptes','discipline'),
(9,'comptes','donneedemo'),
(7,'comptes','etablissement'),
(10,'comptes','journalaudit'),
(11,'comptes','professeur'),
(8,'comptes','utilisateur'),
(1,'contenttypes','contenttype'),
(21,'notes','decisionconseil'),
(22,'notes','note'),
(23,'notes','resultattrimestre'),
(13,'scolarite','anneescolaire'),
(14,'scolarite','classe'),
(18,'scolarite','cours'),
(15,'scolarite','eleve'),
(12,'scolarite','famille'),
(16,'scolarite','inscription'),
(17,'scolarite','matiere'),
(19,'scolarite','paiement'),
(20,'scolarite','trimestre'),
(4,'token_blacklist','blacklistedtoken'),
(5,'token_blacklist','outstandingtoken');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES
(1,'comptes','0001_initial','2026-10-23 11:46:57.580186'),
(2,'scolarite','0001_initial','2026-10-23 11:46:57.752835'),
(3,'absences','0001_initial','2026-10-23 11:46:57.833220'),
(4,'contenttypes','0001_initial','2026-10-23 11:46:57.840147'),
(5,'contenttypes','0002_remove_content_type_name','2026-10-23 11:46:57.857148'),
(6,'auth','0001_initial','2026-10-23 11:46:57.888406'),
(7,'auth','0002_alter_permission_name_max_length','2026-10-23 11:46:57.894866'),
(8,'auth','0003_alter_user_email_max_length','2026-10-23 11:46:57.897491'),
(9,'auth','0004_alter_user_username_opts','2026-10-23 11:46:57.900219'),
(10,'auth','0005_alter_user_last_login_null','2026-10-23 11:46:57.902826'),
(11,'auth','0006_require_contenttypes_0002','2026-10-23 11:46:57.903457'),
(12,'auth','0007_alter_validators_add_error_messages','2026-10-23 11:46:57.905955'),
(13,'auth','0008_alter_user_username_max_length','2026-10-23 11:46:57.908568'),
(14,'auth','0009_alter_user_last_name_max_length','2026-10-23 11:46:57.911333'),
(15,'auth','0010_alter_group_name_max_length','2026-10-23 11:46:57.917038'),
(16,'auth','0011_update_proxy_permissions','2026-10-23 11:46:57.925553'),
(17,'auth','0012_alter_user_first_name_max_length','2026-10-23 11:46:57.929418'),
(18,'comptes','0002_alter_professeur_cin','2026-10-23 11:46:57.936940'),
(19,'notes','0001_initial','2026-10-23 11:46:58.001202'),
(20,'token_blacklist','0001_initial','2026-10-23 11:46:58.031230'),
(21,'token_blacklist','0002_outstandingtoken_jti_hex','2026-10-23 11:46:58.039482'),
(22,'token_blacklist','0003_auto_20171017_2007','2026-10-23 11:46:58.050562'),
(23,'token_blacklist','0004_auto_20171017_2013','2026-10-23 11:46:58.064458'),
(24,'token_blacklist','0005_remove_outstandingtoken_jti','2026-10-23 11:46:58.072686'),
(25,'token_blacklist','0006_auto_20171017_2113','2026-10-23 11:46:58.081819'),
(26,'token_blacklist','0007_auto_20171017_2214','2026-10-23 11:46:58.117436'),
(27,'token_blacklist','0008_migrate_to_bigautofield','2026-10-23 11:46:58.181098'),
(28,'token_blacklist','0010_fix_migrate_to_bigautofield','2026-10-23 11:46:58.190869'),
(29,'token_blacklist','0011_linearizes_history','2026-10-23 11:46:58.191651'),
(30,'token_blacklist','0012_alter_outstandingtoken_user','2026-10-23 11:46:58.199400'),
(31,'token_blacklist','0013_alter_blacklistedtoken_options_and_more','2026-10-23 11:46:58.205311');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `donnee_demo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `donnee_demo` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `modele` varchar(40) NOT NULL,
  `objet_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `donnee_demo_modele_objet_id_2df29289_uniq` (`modele`,`objet_id`)
) ENGINE=InnoDB AUTO_INCREMENT=84 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `donnee_demo` WRITE;
/*!40000 ALTER TABLE `donnee_demo` DISABLE KEYS */;
/*!40000 ALTER TABLE `donnee_demo` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `eleve`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `eleve` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `matricule` varchar(10) NOT NULL,
  `nom` varchar(100) NOT NULL,
  `prenoms` varchar(100) NOT NULL,
  `date_naissance` date NOT NULL,
  `sexe` varchar(10) NOT NULL,
  `adresse` varchar(120) NOT NULL,
  `photo` varchar(100) DEFAULT NULL,
  `observation` varchar(255) NOT NULL,
  `date_creation` datetime(6) NOT NULL,
  `famille_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `matricule` (`matricule`),
  KEY `eleve_nom_86b094_idx` (`nom`,`prenoms`),
  KEY `eleve_famille_id_e13cc743_fk_famille_id` (`famille_id`),
  CONSTRAINT `eleve_famille_id_e13cc743_fk_famille_id` FOREIGN KEY (`famille_id`) REFERENCES `famille` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=41 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `eleve` WRITE;
/*!40000 ALTER TABLE `eleve` DISABLE KEYS */;
/*!40000 ALTER TABLE `eleve` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `etablissement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `etablissement` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  `adresse` varchar(120) NOT NULL,
  `telephone` varchar(10) NOT NULL,
  `email` varchar(150) NOT NULL,
  `logo` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `etablissement` WRITE;
/*!40000 ALTER TABLE `etablissement` DISABLE KEYS */;
INSERT INTO `etablissement` VALUES
(1,'Lycée Ambohitromby','Ambohitromby, Antananarivo, Madagascar','0340000000','contact@ambohitromby.mg','');
/*!40000 ALTER TABLE `etablissement` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `famille`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `famille` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `pere_nom` varchar(100) NOT NULL,
  `pere_prenoms` varchar(100) NOT NULL,
  `mere_nom` varchar(100) NOT NULL,
  `mere_prenoms` varchar(100) NOT NULL,
  `contact_parent` varchar(10) NOT NULL,
  `adresse_parents` varchar(120) NOT NULL,
  `tuteur_nom` varchar(100) NOT NULL,
  `tuteur_prenoms` varchar(100) NOT NULL,
  `tuteur_contact` varchar(10) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `contact_parent` (`contact_parent`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `famille` WRITE;
/*!40000 ALTER TABLE `famille` DISABLE KEYS */;
/*!40000 ALTER TABLE `famille` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `inscription`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `inscription` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `statut` varchar(8) NOT NULL,
  `date_inscription` datetime(6) NOT NULL,
  `annee_id` bigint(20) NOT NULL,
  `classe_id` bigint(20) NOT NULL,
  `eleve_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_inscription_eleve_annee` (`eleve_id`,`annee_id`),
  KEY `inscription_annee_id_9ec7a886_fk_annee_scolaire_id` (`annee_id`),
  KEY `inscription_classe_id_78ae28a0_fk_classe_id` (`classe_id`),
  CONSTRAINT `inscription_annee_id_9ec7a886_fk_annee_scolaire_id` FOREIGN KEY (`annee_id`) REFERENCES `annee_scolaire` (`id`),
  CONSTRAINT `inscription_classe_id_78ae28a0_fk_classe_id` FOREIGN KEY (`classe_id`) REFERENCES `classe` (`id`),
  CONSTRAINT `inscription_eleve_id_f072bf14_fk_eleve_id` FOREIGN KEY (`eleve_id`) REFERENCES `eleve` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=41 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `inscription` WRITE;
/*!40000 ALTER TABLE `inscription` DISABLE KEYS */;
/*!40000 ALTER TABLE `inscription` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `journal_audit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `journal_audit` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `action` varchar(60) NOT NULL,
  `entite` varchar(60) NOT NULL,
  `entite_id` varchar(40) NOT NULL,
  `details` longtext NOT NULL,
  `date` datetime(6) NOT NULL,
  `utilisateur_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `journal_aud_date_ca433f_idx` (`date`),
  KEY `journal_aud_utilisa_6a1b2a_idx` (`utilisateur_id`),
  CONSTRAINT `journal_audit_utilisateur_id_a6c59fba_fk_utilisateur_id` FOREIGN KEY (`utilisateur_id`) REFERENCES `utilisateur` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `journal_audit` WRITE;
/*!40000 ALTER TABLE `journal_audit` DISABLE KEYS */;
/*!40000 ALTER TABLE `journal_audit` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `matiere`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `matiere` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `coefficient` smallint(5) unsigned NOT NULL CHECK (`coefficient` >= 0),
  `classe_id` bigint(20) NOT NULL,
  `discipline_id` bigint(20) NOT NULL,
  `professeur_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_matiere_classe_disc` (`classe_id`,`discipline_id`),
  KEY `matiere_discipline_id_30245249_fk_discipline_id` (`discipline_id`),
  KEY `matiere_professeur_id_20a49138_fk_professeur_id` (`professeur_id`),
  CONSTRAINT `matiere_classe_id_06a36bb1_fk_classe_id` FOREIGN KEY (`classe_id`) REFERENCES `classe` (`id`),
  CONSTRAINT `matiere_discipline_id_30245249_fk_discipline_id` FOREIGN KEY (`discipline_id`) REFERENCES `discipline` (`id`),
  CONSTRAINT `matiere_professeur_id_20a49138_fk_professeur_id` FOREIGN KEY (`professeur_id`) REFERENCES `professeur` (`id`),
  CONSTRAINT `chk_coef` CHECK (`coefficient` >= 1 and `coefficient` <= 6)
) ENGINE=InnoDB AUTO_INCREMENT=43 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `matiere` WRITE;
/*!40000 ALTER TABLE `matiere` DISABLE KEYS */;
/*!40000 ALTER TABLE `matiere` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `note`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `note` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `ds` decimal(4,2) DEFAULT NULL,
  `examen` decimal(4,2) DEFAULT NULL,
  `modifie_le` datetime(6) NOT NULL,
  `inscription_id` bigint(20) NOT NULL,
  `matiere_id` bigint(20) NOT NULL,
  `saisi_par_id` bigint(20) DEFAULT NULL,
  `trimestre_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_note` (`inscription_id`,`matiere_id`,`trimestre_id`),
  KEY `note_matiere_id_1a85238a_fk_matiere_id` (`matiere_id`),
  KEY `note_saisi_par_id_d5fd3cef_fk_utilisateur_id` (`saisi_par_id`),
  KEY `note_trimestre_id_8c12434d_fk_trimestre_id` (`trimestre_id`),
  CONSTRAINT `note_inscription_id_c5fa947e_fk_inscription_id` FOREIGN KEY (`inscription_id`) REFERENCES `inscription` (`id`),
  CONSTRAINT `note_matiere_id_1a85238a_fk_matiere_id` FOREIGN KEY (`matiere_id`) REFERENCES `matiere` (`id`),
  CONSTRAINT `note_saisi_par_id_d5fd3cef_fk_utilisateur_id` FOREIGN KEY (`saisi_par_id`) REFERENCES `utilisateur` (`id`),
  CONSTRAINT `note_trimestre_id_8c12434d_fk_trimestre_id` FOREIGN KEY (`trimestre_id`) REFERENCES `trimestre` (`id`),
  CONSTRAINT `chk_ds` CHECK (`ds` is null or `ds` >= 0 and `ds` <= 20),
  CONSTRAINT `chk_examen` CHECK (`examen` is null or `examen` >= 0 and `examen` <= 20)
) ENGINE=InnoDB AUTO_INCREMENT=481 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `note` WRITE;
/*!40000 ALTER TABLE `note` DISABLE KEYS */;
/*!40000 ALTER TABLE `note` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `paiement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `paiement` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `numero_recu` varchar(20) NOT NULL,
  `droit_inscription` int(10) unsigned NOT NULL CHECK (`droit_inscription` >= 0),
  `caisse_soutien` int(10) unsigned NOT NULL CHECK (`caisse_soutien` >= 0),
  `total` int(10) unsigned NOT NULL CHECK (`total` >= 0),
  `mode_paiement` varchar(30) NOT NULL,
  `date_paiement` datetime(6) NOT NULL,
  `statut` varchar(6) NOT NULL,
  `eleve_matricule` varchar(10) NOT NULL,
  `eleve_nom` varchar(100) NOT NULL,
  `eleve_prenoms` varchar(100) NOT NULL,
  `classe_nom` varchar(50) NOT NULL,
  `annee_id` bigint(20) NOT NULL,
  `enregistre_par_id` bigint(20) DEFAULT NULL,
  `inscription_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `numero_recu` (`numero_recu`),
  UNIQUE KEY `inscription_id` (`inscription_id`),
  KEY `paiement_annee_id_7dba25ab_fk_annee_scolaire_id` (`annee_id`),
  KEY `paiement_enregistre_par_id_a7a5c6ce_fk_utilisateur_id` (`enregistre_par_id`),
  CONSTRAINT `paiement_annee_id_7dba25ab_fk_annee_scolaire_id` FOREIGN KEY (`annee_id`) REFERENCES `annee_scolaire` (`id`),
  CONSTRAINT `paiement_enregistre_par_id_a7a5c6ce_fk_utilisateur_id` FOREIGN KEY (`enregistre_par_id`) REFERENCES `utilisateur` (`id`),
  CONSTRAINT `paiement_inscription_id_f7b7b4f6_fk_inscription_id` FOREIGN KEY (`inscription_id`) REFERENCES `inscription` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=41 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `paiement` WRITE;
/*!40000 ALTER TABLE `paiement` DISABLE KEYS */;
/*!40000 ALTER TABLE `paiement` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `professeur`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `professeur` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `code` varchar(12) DEFAULT NULL,
  `cin` varchar(14) NOT NULL,
  `observation` varchar(255) NOT NULL,
  `discipline_id` bigint(20) NOT NULL,
  `utilisateur_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `cin` (`cin`),
  UNIQUE KEY `utilisateur_id` (`utilisateur_id`),
  UNIQUE KEY `code` (`code`),
  KEY `professeur_discipline_id_58b5859e_fk_discipline_id` (`discipline_id`),
  CONSTRAINT `professeur_discipline_id_58b5859e_fk_discipline_id` FOREIGN KEY (`discipline_id`) REFERENCES `discipline` (`id`),
  CONSTRAINT `professeur_utilisateur_id_30bc17eb_fk_utilisateur_id` FOREIGN KEY (`utilisateur_id`) REFERENCES `utilisateur` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `professeur` WRITE;
/*!40000 ALTER TABLE `professeur` DISABLE KEYS */;
/*!40000 ALTER TABLE `professeur` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `resultat_trimestre`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `resultat_trimestre` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `total_coefficients` int(10) unsigned NOT NULL CHECK (`total_coefficients` >= 0),
  `total_points` decimal(8,2) NOT NULL,
  `moyenne` decimal(5,2) NOT NULL,
  `rang` int(10) unsigned DEFAULT NULL CHECK (`rang` >= 0),
  `effectif_classe` int(10) unsigned NOT NULL CHECK (`effectif_classe` >= 0),
  `inscription_id` bigint(20) NOT NULL,
  `trimestre_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_resultat` (`inscription_id`,`trimestre_id`),
  KEY `resultat_trimestre_trimestre_id_32fd7a7a_fk_trimestre_id` (`trimestre_id`),
  CONSTRAINT `resultat_trimestre_inscription_id_97f5e8ab_fk_inscription_id` FOREIGN KEY (`inscription_id`) REFERENCES `inscription` (`id`),
  CONSTRAINT `resultat_trimestre_trimestre_id_32fd7a7a_fk_trimestre_id` FOREIGN KEY (`trimestre_id`) REFERENCES `trimestre` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=81 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `resultat_trimestre` WRITE;
/*!40000 ALTER TABLE `resultat_trimestre` DISABLE KEYS */;
/*!40000 ALTER TABLE `resultat_trimestre` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `token_blacklist_blacklistedtoken`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `token_blacklist_blacklistedtoken` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `blacklisted_at` datetime(6) NOT NULL,
  `token_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `token_id` (`token_id`),
  CONSTRAINT `token_blacklist_blacklistedtoken_token_id_3cc7fe56_fk` FOREIGN KEY (`token_id`) REFERENCES `token_blacklist_outstandingtoken` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `token_blacklist_blacklistedtoken` WRITE;
/*!40000 ALTER TABLE `token_blacklist_blacklistedtoken` DISABLE KEYS */;
/*!40000 ALTER TABLE `token_blacklist_blacklistedtoken` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `token_blacklist_outstandingtoken`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `token_blacklist_outstandingtoken` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `token` longtext NOT NULL,
  `created_at` datetime(6) DEFAULT NULL,
  `expires_at` datetime(6) NOT NULL,
  `user_id` bigint(20) DEFAULT NULL,
  `jti` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `token_blacklist_outstandingtoken_jti_hex_d9bdf6f7_uniq` (`jti`),
  KEY `token_blacklist_outs_user_id_83bc629a_fk_utilisate` (`user_id`),
  CONSTRAINT `token_blacklist_outs_user_id_83bc629a_fk_utilisate` FOREIGN KEY (`user_id`) REFERENCES `utilisateur` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `token_blacklist_outstandingtoken` WRITE;
/*!40000 ALTER TABLE `token_blacklist_outstandingtoken` DISABLE KEYS */;
/*!40000 ALTER TABLE `token_blacklist_outstandingtoken` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `trimestre`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `trimestre` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `numero` smallint(5) unsigned NOT NULL CHECK (`numero` >= 0),
  `date_debut` date NOT NULL,
  `date_fin` date NOT NULL,
  `cloture` tinyint(1) NOT NULL,
  `annee_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_trimestre` (`annee_id`,`numero`),
  CONSTRAINT `trimestre_annee_id_0692d2a9_fk_annee_scolaire_id` FOREIGN KEY (`annee_id`) REFERENCES `annee_scolaire` (`id`),
  CONSTRAINT `chk_trim_num` CHECK (`numero` >= 1 and `numero` <= 3)
) ENGINE=InnoDB AUTO_INCREMENT=79 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `trimestre` WRITE;
/*!40000 ALTER TABLE `trimestre` DISABLE KEYS */;
INSERT INTO `trimestre` VALUES
(1,1,'2020-10-01','2020-12-31',0,1),
(2,2,'2021-01-01','2021-03-31',0,1),
(3,3,'2021-04-01','2021-06-30',0,1),
(4,1,'2021-10-01','2021-12-31',0,2),
(5,2,'2022-01-01','2022-03-31',0,2),
(6,3,'2022-04-01','2022-06-30',0,2),
(7,1,'2022-10-01','2022-12-31',0,3),
(8,2,'2023-01-01','2023-03-31',0,3),
(9,3,'2023-04-01','2023-06-30',0,3),
(10,1,'2023-10-01','2023-12-31',0,4),
(11,2,'2024-01-01','2024-03-31',0,4),
(12,3,'2024-04-01','2024-06-30',0,4),
(13,1,'2024-10-01','2024-12-31',0,5),
(14,2,'2025-01-01','2025-03-31',0,5),
(15,3,'2025-04-01','2025-06-30',0,5),
(16,1,'2025-10-01','2025-12-31',0,6),
(17,2,'2026-01-01','2026-03-31',0,6),
(18,3,'2026-04-01','2026-06-30',0,6),
(19,1,'2026-10-01','2026-12-31',0,7),
(20,2,'2027-01-01','2027-03-31',0,7),
(21,3,'2027-04-01','2027-06-30',0,7),
(22,1,'2027-10-01','2027-12-31',0,8),
(23,2,'2028-01-01','2028-03-31',0,8),
(24,3,'2028-04-01','2028-06-30',0,8),
(25,1,'2028-10-01','2028-12-31',0,9),
(26,2,'2029-01-01','2029-03-31',0,9),
(27,3,'2029-04-01','2029-06-30',0,9),
(28,1,'2029-10-01','2029-12-31',0,10),
(29,2,'2030-01-01','2030-03-31',0,10),
(30,3,'2030-04-01','2030-06-30',0,10),
(31,1,'2030-10-01','2030-12-31',0,11),
(32,2,'2031-01-01','2031-03-31',0,11),
(33,3,'2031-04-01','2031-06-30',0,11),
(34,1,'2031-10-01','2031-12-31',0,12),
(35,2,'2032-01-01','2032-03-31',0,12),
(36,3,'2032-04-01','2032-06-30',0,12),
(37,1,'2032-10-01','2032-12-31',0,13),
(38,2,'2033-01-01','2033-03-31',0,13),
(39,3,'2033-04-01','2033-06-30',0,13),
(40,1,'2033-10-01','2033-12-31',0,14),
(41,2,'2034-01-01','2034-03-31',0,14),
(42,3,'2034-04-01','2034-06-30',0,14),
(43,1,'2034-10-01','2034-12-31',0,15),
(44,2,'2035-01-01','2035-03-31',0,15),
(45,3,'2035-04-01','2035-06-30',0,15),
(46,1,'2035-10-01','2035-12-31',0,16),
(47,2,'2036-01-01','2036-03-31',0,16),
(48,3,'2036-04-01','2036-06-30',0,16),
(49,1,'2036-10-01','2036-12-31',0,17),
(50,2,'2037-01-01','2037-03-31',0,17),
(51,3,'2037-04-01','2037-06-30',0,17),
(52,1,'2037-10-01','2037-12-31',0,18),
(53,2,'2038-01-01','2038-03-31',0,18),
(54,3,'2038-04-01','2038-06-30',0,18),
(55,1,'2038-10-01','2038-12-31',0,19),
(56,2,'2039-01-01','2039-03-31',0,19),
(57,3,'2039-04-01','2039-06-30',0,19),
(58,1,'2039-10-01','2039-12-31',0,20),
(59,2,'2040-01-01','2040-03-31',0,20),
(60,3,'2040-04-01','2040-06-30',0,20),
(61,1,'2040-10-01','2040-12-31',0,21),
(62,2,'2041-01-01','2041-03-31',0,21),
(63,3,'2041-04-01','2041-06-30',0,21),
(64,1,'2041-10-01','2041-12-31',0,22),
(65,2,'2042-01-01','2042-03-31',0,22),
(66,3,'2042-04-01','2042-06-30',0,22),
(67,1,'2042-10-01','2042-12-31',0,23),
(68,2,'2043-01-01','2043-03-31',0,23),
(69,3,'2043-04-01','2043-06-30',0,23),
(70,1,'2043-10-01','2043-12-31',0,24),
(71,2,'2044-01-01','2044-03-31',0,24),
(72,3,'2044-04-01','2044-06-30',0,24),
(73,1,'2044-10-01','2044-12-31',0,25),
(74,2,'2045-01-01','2045-03-31',0,25),
(75,3,'2045-04-01','2045-06-30',0,25),
(76,1,'2045-10-01','2045-12-31',0,26),
(77,2,'2046-01-01','2046-03-31',0,26),
(78,3,'2046-04-01','2046-06-30',0,26);
/*!40000 ALTER TABLE `trimestre` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `utilisateur`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `utilisateur` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `email` varchar(150) NOT NULL,
  `role` varchar(12) NOT NULL,
  `nom` varchar(100) NOT NULL,
  `prenom` varchar(100) NOT NULL,
  `date_naissance` date DEFAULT NULL,
  `sexe` varchar(10) NOT NULL,
  `adresse` varchar(120) NOT NULL,
  `telephone` varchar(10) NOT NULL,
  `photo` varchar(100) DEFAULT NULL,
  `statut` varchar(12) NOT NULL,
  `theme` varchar(6) NOT NULL,
  `doit_changer_mdp` tinyint(1) NOT NULL,
  `tentatives_echec` smallint(5) unsigned NOT NULL CHECK (`tentatives_echec` >= 0),
  `verrouille_jusqu_a` datetime(6) DEFAULT NULL,
  `date_creation` datetime(6) NOT NULL,
  `annee_preferee` smallint(5) unsigned DEFAULT NULL CHECK (`annee_preferee` >= 0),
  `motif_refus` varchar(255) NOT NULL,
  `valide_par_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `telephone` (`telephone`),
  KEY `utilisateur_role_0c32ad_idx` (`role`,`statut`),
  KEY `utilisateur_valide_par_id_bb890d95_fk_utilisateur_id` (`valide_par_id`),
  CONSTRAINT `utilisateur_valide_par_id_bb890d95_fk_utilisateur_id` FOREIGN KEY (`valide_par_id`) REFERENCES `utilisateur` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `utilisateur` WRITE;
/*!40000 ALTER TABLE `utilisateur` DISABLE KEYS */;
/*!40000 ALTER TABLE `utilisateur` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

