-- Crear tabla de usuarios (según tu imagen)
CREATE TABLE IF NOT EXISTS usuarios (
    id INT(11) AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(200) NOT NULL UNIQUE COMMENT 'Nombre de usuario para iniciar sesión',
    password VARCHAR(200) NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    estado TINYINT(4) NOT NULL DEFAULT 0,
    rol TINYINT(4) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Crear tabla de historial de chat
CREATE TABLE IF NOT EXISTS historial_chat (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT(11) NOT NULL,
    pregunta TEXT NOT NULL,
    respuesta TEXT NOT NULL,
    rol_ia VARCHAR(50) NOT NULL COMMENT 'leyes, ortografia o sgsp',
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;