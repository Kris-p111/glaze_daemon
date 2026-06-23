-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Server version:               11.5.2-MariaDB - mariadb.org binary distribution
-- Server OS:                    Win64
-- HeidiSQL Version:             12.6.0.6765
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Dumping database structure for tilearchive
CREATE DATABASE IF NOT EXISTS `tilearchive` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `tilearchive`;

-- Dumping structure for table tilearchive.compound
CREATE TABLE IF NOT EXISTS `compound` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `Symbol` varchar(10) NOT NULL,
  `Name` varchar(100) NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `Symbol` (`Symbol`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='化合';

-- Dumping data for table tilearchive.compound: ~0 rows (approximately)

-- Dumping structure for table tilearchive.compound_glazetype
CREATE TABLE IF NOT EXISTS `compound_glazetype` (
  `CompoundID` int(10) unsigned NOT NULL,
  `GlazeTypeID` int(10) unsigned NOT NULL,
  PRIMARY KEY (`CompoundID`,`GlazeTypeID`),
  KEY `GlazeTypeID` (`GlazeTypeID`),
  CONSTRAINT `compound_glazetype_ibfk_1` FOREIGN KEY (`CompoundID`) REFERENCES `compound` (`ID`) ON DELETE CASCADE,
  CONSTRAINT `compound_glazetype_ibfk_2` FOREIGN KEY (`GlazeTypeID`) REFERENCES `glazetype` (`ID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='化合 <-> 釉薬の種類';

-- Dumping data for table tilearchive.compound_glazetype: ~0 rows (approximately)

-- Dumping structure for table tilearchive.glazetype
CREATE TABLE IF NOT EXISTS `glazetype` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `Name` varchar(100) NOT NULL,
  `Description` mediumtext DEFAULT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `Name` (`Name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='釉薬の種類';

-- Dumping data for table tilearchive.glazetype: ~0 rows (approximately)

-- Dumping structure for table tilearchive.simplifiedcolor
CREATE TABLE IF NOT EXISTS `simplifiedcolor` (
  `ID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `Name` varchar(100) NOT NULL,
  PRIMARY KEY (`ID`) USING BTREE,
  UNIQUE KEY `Name` (`Name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='簡略化された色';

-- Dumping data for table tilearchive.simplifiedcolor: ~0 rows (approximately)

-- Dumping structure for table tilearchive.surfacecondition
CREATE TABLE IF NOT EXISTS `surfacecondition` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `Name` varchar(100) NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `Name` (`Name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='表面状態';

-- Dumping data for table tilearchive.surfacecondition: ~0 rows (approximately)

-- Dumping structure for table tilearchive.technique
CREATE TABLE IF NOT EXISTS `technique` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `Type` varchar(100) NOT NULL,
  UNIQUE KEY `Type` (`Type`),
  KEY `ID` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='技法';

-- Dumping data for table tilearchive.technique: ~0 rows (approximately)

-- Dumping structure for table tilearchive.testpiece
CREATE TABLE IF NOT EXISTS `testpiece` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `BoardID` int(10) unsigned NOT NULL,
  `Image` mediumblob DEFAULT NULL,
  `Color_L` float DEFAULT NULL,
  `Color_A` float DEFAULT NULL,
  `Color_B` float DEFAULT NULL,
  `GlazeTypeID` int(10) unsigned DEFAULT NULL,
  `FiringTemperature` int(11) DEFAULT NULL,
  `ChemicalComposition` mediumtext DEFAULT NULL,
  `SurfaceConditionID` int(10) unsigned DEFAULT NULL,
  `EntryDate` date DEFAULT NULL,
  `FiringType` mediumtext DEFAULT NULL,
  `SoilType` mediumtext DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `idx_testpiece_colorL` (`Color_L`),
  KEY `idx_testpiece_colorA` (`Color_A`),
  KEY `idx_testpiece_colorB` (`Color_B`),
  KEY `idx_testpiece_firingtemp` (`FiringTemperature`),
  KEY `idx_testpiece_firingtype` (`FiringType`(768)),
  KEY `idx_testpiece_entrydate` (`EntryDate`),
  KEY `idx_testpiece_glazetype` (`GlazeTypeID`),
  KEY `idx_testpiece_surfacecondition` (`SurfaceConditionID`),
  KEY `idx_testpiece_board` (`BoardID`),
  KEY `idx_soil_type` (`SoilType`(768)),
  FULLTEXT KEY `ft_chemical` (`ChemicalComposition`),
  CONSTRAINT `testpiece_ibfk_1` FOREIGN KEY (`BoardID`) REFERENCES `tileboard` (`ID`) ON DELETE CASCADE,
  CONSTRAINT `testpiece_ibfk_2` FOREIGN KEY (`GlazeTypeID`) REFERENCES `glazetype` (`ID`),
  CONSTRAINT `testpiece_ibfk_3` FOREIGN KEY (`SurfaceConditionID`) REFERENCES `surfacecondition` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='テストピース\r\n\r\nto-do:\r\nFiringType & SoilType -> Tables\r\n+ more glaze IDs (ato de)\r\n- ChemicalComposition\r\nStore type -> binary data for images ((6-bit)UU encode)';

-- Dumping data for table tilearchive.testpiece: ~0 rows (approximately)

-- Dumping structure for table tilearchive.tileboard
CREATE TABLE IF NOT EXISTS `tileboard` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `Image` mediumtext DEFAULT NULL,
  `TileCount` int(11) DEFAULT NULL,
  `Description` mediumtext DEFAULT NULL,
  `CreatedBy` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  FULLTEXT KEY `ft_description` (`Description`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='テストボード';

-- Dumping data for table tilearchive.tileboard: ~0 rows (approximately)
INSERT INTO `tileboard` (`ID`, `Image`, `TileCount`, `Description`, `CreatedBy`) VALUES
	(1, NULL, NULL, NULL, NULL);

-- Dumping structure for table tilearchive.tile_color
CREATE TABLE IF NOT EXISTS `tile_color` (
  `TileID` int(11) unsigned NOT NULL,
  `ColorID` int(11) unsigned NOT NULL,
  `ColorName` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`TileID`,`ColorID`),
  KEY `ColorName` (`ColorName`),
  KEY `ColorID` (`ColorID`) USING BTREE,
  CONSTRAINT `FK_tile_color_ceramictile` FOREIGN KEY (`TileID`) REFERENCES `testpiece` (`ID`) ON DELETE CASCADE,
  CONSTRAINT `FK_tile_color_simplifiedcolor` FOREIGN KEY (`ColorID`) REFERENCES `simplifiedcolor` (`ID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='テストピースの色';

-- Dumping data for table tilearchive.tile_color: ~0 rows (approximately)

-- Dumping structure for table tilearchive.tile_compound
CREATE TABLE IF NOT EXISTS `tile_compound` (
  `TileID` int(10) unsigned NOT NULL,
  `CompoundID` int(10) unsigned NOT NULL,
  PRIMARY KEY (`TileID`,`CompoundID`) USING BTREE,
  KEY `CompoundID` (`CompoundID`) USING BTREE,
  CONSTRAINT `tile_compound_ibfk_1` FOREIGN KEY (`TileID`) REFERENCES `testpiece` (`ID`) ON DELETE CASCADE,
  CONSTRAINT `tile_compound_ibfk_2` FOREIGN KEY (`CompoundID`) REFERENCES `compound` (`ID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='テストピース <-> 化合';

-- Dumping data for table tilearchive.tile_compound: ~0 rows (approximately)

-- Dumping structure for table tilearchive.tile_technique
CREATE TABLE IF NOT EXISTS `tile_technique` (
  `TestPieceID` int(10) unsigned NOT NULL,
  `TechniqueID` int(10) unsigned NOT NULL,
  PRIMARY KEY (`TestPieceID`,`TechniqueID`),
  KEY `TechniqueID` (`TechniqueID`),
  CONSTRAINT `tile_technique_ibfk_1` FOREIGN KEY (`TestPieceID`) REFERENCES `testpiece` (`ID`) ON DELETE CASCADE,
  CONSTRAINT `tile_technique_ibfk_2` FOREIGN KEY (`TechniqueID`) REFERENCES `technique` (`ID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='テストピース <-> 技法';

-- Dumping data for table tilearchive.tile_technique: ~0 rows (approximately)

-- Dumping structure for view tilearchive.view_testpiece_full
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `view_testpiece_full` (
	`ID` INT(10) UNSIGNED NOT NULL,
	`Image` MEDIUMTEXT NULL COLLATE 'utf8mb4_unicode_ci',
	`Color_L` FLOAT NULL,
	`Color_A` FLOAT NULL,
	`Color_B` FLOAT NULL,
	`GlazeType` VARCHAR(100) NULL COLLATE 'utf8mb4_unicode_ci',
	`SurfaceCondition` VARCHAR(100) NULL COLLATE 'utf8mb4_unicode_ci',
	`BoardID` INT(10) UNSIGNED NULL,
	`CreatedBy` VARCHAR(100) NULL COLLATE 'utf8mb4_unicode_ci',
	`EntryDate` DATE NULL,
	`FiringType` MEDIUMTEXT NULL COLLATE 'utf8mb4_unicode_ci',
	`FiringTemperature` INT(11) NULL,
	`SoilType` MEDIUMTEXT NULL COLLATE 'utf8mb4_unicode_ci'
) ENGINE=MyISAM;

-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `view_testpiece_full`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `view_testpiece_full` AS SELECT 
  tp.ID,
  tp.Image,
  tp.Color_L, tp.Color_A, tp.Color_B,
  gt.Name AS GlazeType,
  sc.Name AS SurfaceCondition,
  tb.ID AS BoardID,
  tb.CreatedBy,
  tp.EntryDate,
  tp.FiringType,
  tp.FiringTemperature,
  tp.SoilType
FROM testpiece tp
LEFT JOIN glazetype gt ON tp.GlazeTypeID = gt.ID
LEFT JOIN surfacecondition sc ON tp.SurfaceConditionID = sc.ID
LEFT JOIN tileboard tb ON tp.BoardID = tb.ID ;

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
