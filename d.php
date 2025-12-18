<?php
// ==========================
// 🔹 DATABASE CONFIGURATION
// ==========================
$servername = "localhost"; // Server name (usually localhost)
$username   = "root";      // MySQL username (default: root)
$password   = "";          // MySQL password (empty by default in XAMPP)
$database   = "testdb";    // The name of your database (create it in phpMyAdmin)

// ==========================
// 🔹 CONNECT TO DATABASE
// ==========================
$conn = new mysqli($servername, $username, $password, $database);

// Check connection
if ($conn->connect_error) {
    die("❌ Connection failed: " . $conn->connect_error);
}

echo "✅ Connected to database successfully!<br>";

// ==========================
// 🔹 OPTIONAL: CREATE FUNCTION
// ==========================
// You can reuse this function anywhere in your project.
function getConnection() {
    $servername = "localhost";
    $username   = "root";
    $password   = "";
    $database   = "testdb";

    $conn = new mysqli($servername, $username, $password, $database);

    if ($conn->connect_error) {
        die("❌ Connection failed: " . $conn->connect_error);
    }
    return $conn;
}

// Example usage of the function
$conn2 = getConnection();
echo "✅ Second connection using function is also successful!";

// Close connections
$conn->close();
$conn2->close();
?>
