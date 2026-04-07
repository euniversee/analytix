-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 06, 2026 at 02:00 AM
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
-- Database: `datapenjualan`
--
CREATE DATABASE IF NOT EXISTS `datapenjualan` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `datapenjualan`;

-- --------------------------------------------------------

--
-- Table structure for table `penjualan`
--

CREATE TABLE `penjualan` (
  `id` int(11) NOT NULL,
  `customer_name` varchar(255) NOT NULL,
  `date` date NOT NULL,
  `purchase_amount` decimal(15,2) NOT NULL,
  `payment_status` enum('Success','Failed') NOT NULL DEFAULT 'Success',
  `note` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `penjualan`
--

INSERT INTO `penjualan` (`id`, `customer_name`, `date`, `purchase_amount`, `payment_status`, `note`) VALUES
(1, 'Sigit Ramadhan', '2025-01-12', 2400000.00, 'Success', ''),
(2, 'Dwi Santoso', '2025-01-14', 850000.00, 'Failed', 'Card declined'),
(3, 'Andi Pratama', '2025-01-16', 3100000.00, 'Success', ''),
(4, 'Rahma Hapsari', '2025-01-18', 560000.00, 'Success', ''),
(5, 'Bagas Nugroho', '2025-01-19', 1750000.00, 'Failed', ''),
(6, 'Citra Dewi', '2024-12-05', 2200000.00, 'Success', ''),
(7, 'Fajar Kusuma', '2024-12-12', 1800000.00, 'Success', ''),
(8, 'Nadia Putri', '2024-12-22', 1200000.00, 'Success', '');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `penjualan`
--
ALTER TABLE `penjualan`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `penjualan`
--
ALTER TABLE `penjualan`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
