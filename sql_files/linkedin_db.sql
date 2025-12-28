-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Dec 28, 2025 at 06:03 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `linkedin_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `li_person`
--

CREATE TABLE `li_person` (
  `task_id` varchar(30) NOT NULL,
  `name` varchar(50) NOT NULL,
  `headline` varchar(150) NOT NULL,
  `location` varchar(150) NOT NULL,
  `connections` varchar(20) NOT NULL,
  `last_activity` varchar(20) NOT NULL,
  `profile_url` text NOT NULL,
  `job_title` varchar(100) NOT NULL,
  `company_name` varchar(120) NOT NULL,
  `company_link` text NOT NULL,
  `work_mode` varchar(50) NOT NULL,
  `total_duration` varchar(50) NOT NULL,
  `job_type` varchar(50) NOT NULL,
  `duration` varchar(50) NOT NULL,
  `tenurity` varchar(50) NOT NULL,
  `skills` text NOT NULL,
  `experience_json` text NOT NULL,
  `inserted_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `li_person_master`
--

CREATE TABLE `li_person_master` (
  `task_id` varchar(30) NOT NULL,
  `name` varchar(50) NOT NULL,
  `headline` varchar(150) NOT NULL,
  `location` varchar(150) NOT NULL,
  `connections` varchar(20) NOT NULL,
  `last_activity` varchar(20) NOT NULL,
  `profile_url` text NOT NULL,
  `job_title` varchar(100) NOT NULL,
  `company_name` varchar(120) NOT NULL,
  `company_link` text NOT NULL,
  `work_mode` varchar(50) NOT NULL,
  `total_duration` varchar(50) NOT NULL,
  `job_type` varchar(50) NOT NULL,
  `duration` varchar(50) NOT NULL,
  `tenurity` varchar(50) NOT NULL,
  `skills` text NOT NULL,
  `experience_json` text NOT NULL,
  `inserted_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `li_person`
--
ALTER TABLE `li_person`
  ADD PRIMARY KEY (`task_id`),
  ADD KEY `task_id` (`task_id`);

--
-- Indexes for table `li_person_master`
--
ALTER TABLE `li_person_master`
  ADD PRIMARY KEY (`task_id`),
  ADD UNIQUE KEY `person_link` (`profile_url`) USING HASH,
  ADD KEY `task_id` (`task_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
