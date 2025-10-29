import os
import sys
import logging
import shutil
import hashlib
import random
import subprocess
import argparse
import zipfile
import time
from datetime import datetime

logger = logging.getLogger("7ZipFuzzer")


def setup_logger(debug=False):
    """Настройка системы логирования"""
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Консольный вывод
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Файловый вывод
    log_file = f"7zip_fuzzer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return log_file


class SevenZipFuzzer:
    def __init__(self, base_zip_path, sevenzip_path=None, debug=False):
        self.base_zip_path = base_zip_path
        self.sevenzip_path = sevenzip_path or self.find_7zip()
        self.debug = debug
        self.crash_count = 0
        self.iteration_count = 0
        self.start_time = None

        # Проверки
        if not os.path.exists(self.base_zip_path):
            logger.error(f"Base ZIP file not found: {self.base_zip_path}")
            sys.exit(1)

        if not self.sevenzip_path:
            logger.error("7zip not found! Please specify path with --sevenzip-path")
            sys.exit(1)

        logger.info(f"7zip path: {self.sevenzip_path}")
        logger.info(f"Base ZIP: {self.base_zip_path}")

    def find_7zip(self):
        """Автоматически ищет 7zip в стандартных местах"""
        possible_paths = [
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
            r"C:\Program Files\7-Zip\7zG.exe",
            r"C:\Program Files (x86)\7-Zip\7zG.exe",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def create_base_zip(self):
        """Создает базовый ZIP файл если он не существует"""
        if not os.path.exists(self.base_zip_path):
            logger.info(f"Creating base ZIP file: {self.base_zip_path}")
            with zipfile.ZipFile(self.base_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Добавляем разнообразные тестовые файлы
                zipf.writestr("normal_file.txt", "This is a normal text file for fuzzing" * 10)
                zipf.writestr("binary_data.bin", bytes([i % 256 for i in range(1000)]))
                zipf.writestr("empty_file.txt", "")
                zipf.writestr("folder/nested_file.txt", "Nested file content")
                zipf.writestr("very_long_name_" + "x" * 100 + ".txt", "File with long name")

            logger.info("Base ZIP file created successfully")

    def mutate_zip_structure(self, data):
        """Основная функция мутации ZIP структуры"""
        if len(data) == 0:
            return data

        mutated_data = bytearray(data)
        mutation_type = random.randint(1, 10)

        try:
            if mutation_type == 1:
                return self._corrupt_local_headers(mutated_data)
            elif mutation_type == 2:
                return self._corrupt_central_directory(mutated_data)
            elif mutation_type == 3:
                return self._mutate_compression_methods(mutated_data)
            elif mutation_type == 4:
                return self._corrupt_crc_values(mutated_data)
            elif mutation_type == 5:
                return self._mutate_file_sizes(mutated_data)
            elif mutation_type == 6:
                return self._inject_random_headers(mutated_data)
            elif mutation_type == 7:
                return self._bit_flip_mutation(mutated_data)
            elif mutation_type == 8:
                return self._boundary_value_mutation(mutated_data)
            elif mutation_type == 9:
                return self._repeat_byte_mutation(mutated_data)
            else:
                return self._arithmetic_mutation(mutated_data)

        except Exception as e:
            logger.warning(f"Mutation failed: {e}, using bit flip fallback")
            return self._bit_flip_mutation(mutated_data)

    def _corrupt_local_headers(self, data):
        """Портит локальные заголовки файлов"""
        signature = b'\x50\x4B\x03\x04'
        pos = 0

        while pos < len(data) - 4:
            if data[pos:pos + 4] == signature:
                # Мутируем различные поля заголовка
                header_size = min(30, len(data) - pos)
                for i in range(4, header_size):
                    if random.random() < 0.4:
                        data[pos + i] = random.randint(0, 255)
                pos += header_size
            pos += 1

        return bytes(data)

    def _corrupt_central_directory(self, data):
        """Портит центральный каталог"""
        signature = b'\x50\x4B\x01\x02'
        pos = 0

        while pos < len(data) - 4:
            if data[pos:pos + 4] == signature:
                # Мутируем записи центрального каталога
                header_size = min(46, len(data) - pos)
                for i in range(4, header_size):
                    if random.random() < 0.3:
                        data[pos + i] = random.randint(0, 255)
                pos += header_size
            pos += 1

        return bytes(data)

    def _mutate_compression_methods(self, data):
        """Мутирует методы сжатия"""
        local_sig = b'\x50\x4B\x03\x04'
        central_sig = b'\x50\x4B\x01\x02'

        for signature in [local_sig, central_sig]:
            pos = 0
            while pos < len(data) - 8:
                if data[pos:pos + 4] == signature:
                    # Метод сжатия на позиции +8
                    if pos + 8 < len(data):
                        # 0 - stored, 8 - deflated, 9 - deflate64, etc.
                        data[pos + 8] = random.choice([0, 1, 8, 9, 12, 14, 96, 99, 255])
                pos += 1

        return bytes(data)

    def _corrupt_crc_values(self, data):
        """Портит CRC32 значения"""
        signatures = [b'\x50\x4B\x03\x04', b'\x50\x4B\x01\x02']

        for signature in signatures:
            pos = 0
            while pos < len(data) - 16:
                if data[pos:pos + 4] == signature:
                    # CRC32 находится по смещению +14 от локального заголовка
                    # и +16 от центрального заголовка
                    crc_offset = 14 if signature == b'\x50\x4B\x03\x04' else 16
                    if pos + crc_offset + 4 < len(data):
                        for i in range(4):
                            data[pos + crc_offset + i] = random.randint(0, 255)
                pos += 1

        return bytes(data)

    def _mutate_file_sizes(self, data):
        """Мутирует размеры файлов"""
        signature = b'\x50\x4B\x03\x04'
        pos = 0

        while pos < len(data) - 26:
            if data[pos:pos + 4] == signature:
                # Сжатый размер (смещение +18) и несжатый размер (смещение +22)
                for offset in [18, 22]:
                    if pos + offset + 4 < len(data):
                        # Генерируем случайный размер
                        size = random.randint(0, 0xFFFFFFFF)
                        for i in range(4):
                            data[pos + offset + i] = (size >> (i * 8)) & 0xFF
                pos += 30
            pos += 1

        return bytes(data)

    def _inject_random_headers(self, data):
        """Внедряет случайные ZIP заголовки"""
        headers = [
            b'\x50\x4B\x03\x04',  # Local file header
            b'\x50\x4B\x01\x02',  # Central directory
            b'\x50\x4B\x05\x06',  # End of central directory
            b'\x50\x4B\x06\x07',  # Zip64 end of central directory
            b'\x50\x4B\x07\x08',  # Zip64 end of central directory locator
            b'\x50\x4B\x08\x07',  # Data descriptor
        ]

        if len(data) < 5000:  # Добавляем заголовки только в небольшие файлы
            header = random.choice(headers)
            position = random.randint(0, len(data))
            extra_data = bytearray(os.urandom(random.randint(10, 100)))
            new_data = bytearray(data)
            new_data[position:position] = bytearray(header) + extra_data
            return bytes(new_data)

        return bytes(data)

    def _bit_flip_mutation(self, data):
        """Битовая мутация случайных байтов"""
        num_mutations = random.randint(1, min(100, len(data) // 10))

        for _ in range(num_mutations):
            if len(data) == 0:
                break
            pos = random.randint(0, len(data) - 1)
            bit_mask = 1 << random.randint(0, 7)
            data[pos] ^= bit_mask

        return bytes(data)

    def _boundary_value_mutation(self, data):
        """Мутация граничными значениями"""
        boundary_values = [0x00, 0xFF, 0x7F, 0x80, 0xFFFF, 0xFFFFFFFF]

        if len(data) > 10:
            num_mutations = random.randint(1, 20)
            for _ in range(num_mutations):
                pos = random.randint(0, len(data) - 1)
                if random.random() < 0.3:
                    # Заменяем на граничное значение (только младший байт)
                    value = random.choice(boundary_values) & 0xFF
                    data[pos] = value
                else:
                    # Заменяем последовательность байтов
                    length = random.randint(2, min(8, len(data) - pos))
                    for i in range(length):
                        if pos + i < len(data):
                            value = random.choice(boundary_values)
                            for j in range(min(4, length - i)):
                                if pos + i + j < len(data):
                                    data[pos + i + j] = (value >> (j * 8)) & 0xFF
                    break

        return bytes(data)

    def _repeat_byte_mutation(self, data):
        """Мутация повторяющимися байтами"""
        if len(data) > 20:
            pattern = random.randint(0, 255)
            start_pos = random.randint(0, len(data) - 10)
            length = random.randint(5, min(50, len(data) - start_pos))

            for i in range(length):
                if start_pos + i < len(data):
                    data[start_pos + i] = pattern

        return bytes(data)

    def _arithmetic_mutation(self, data):
        """Арифметическая мутация"""
        if len(data) > 10:
            pos = random.randint(0, len(data) - 1)
            operation = random.choice(['add', 'sub', 'mul'])
            value = random.randint(1, 255)

            if operation == 'add':
                data[pos] = (data[pos] + value) & 0xFF
            elif operation == 'sub':
                data[pos] = (data[pos] - value) & 0xFF
            elif operation == 'mul':
                data[pos] = (data[pos] * value) & 0xFF

        return bytes(data)

    def run_7zip_test(self, test_file_path):
        """Запускает 7zip для тестирования файла"""
        try:
            # Команда для тестирования архива
            cmd = [self.sevenzip_path, "t", test_file_path]

            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15,  # Увеличиваем таймаут для больших файлов
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            return self.analyze_7zip_result(process), process

        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout testing file: {test_file_path}")
            return True, None
        except Exception as e:
            logger.error(f"Error testing file {test_file_path}: {e}")
            return False, None

    def analyze_7zip_result(self, process_result):
        """Анализирует результат выполнения 7zip"""
        if process_result is None:
            return True  # Таймаут считаем за потенциальный сбой

        stdout = process_result.stdout.decode('utf-8', errors='ignore')
        stderr = process_result.stderr.decode('utf-8', errors='ignore')

        # Признаки критических ошибок в 7zip
        crash_indicators = [
            'Exception',
            'Access violation',
            'Segmentation fault',
            'CRASH',
            'Stack overflow',
            'Heap corruption',
            'Fatal error',
            'Internal error'
        ]

        # 7zip коды возврата: 0 - OK, 1 - Warning, 2 - Fatal error, 7 - Command line error, 8 - Not enough memory
        if process_result.returncode == 2:
            logger.debug("7zip fatal error (return code 2)")
            return True

        if process_result.returncode == 8:
            logger.debug("7zip memory error (return code 8)")
            return True

        if any(indicator in stdout for indicator in crash_indicators) or \
                any(indicator in stderr for indicator in crash_indicators):
            logger.debug("Crash indicator found in output")
            return True

        return False

    def save_crash(self, iteration, data, process_result):
        """Сохраняет информацию о сбое"""
        self.crash_count += 1
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        crash_dir = f"crashes/crash_{timestamp}_iter_{iteration}"
        os.makedirs(crash_dir, exist_ok=True)

        try:
            # Сохраняем мутированный файл
            crash_file = os.path.join(crash_dir, "crash.zip")
            with open(crash_file, 'wb') as f:
                f.write(data)

            # Сохраняем информацию о выполнении
            info_file = os.path.join(crash_dir, "info.txt")
            with open(info_file, 'w', encoding='utf-8') as f:
                f.write(f"7Zip Fuzzer Crash Report\n")
                f.write(f"Timestamp: {datetime.now()}\n")
                f.write(f"Iteration: {iteration}\n")
                f.write(f"File size: {len(data)} bytes\n")
                f.write(f"File hash (MD5): {hashlib.md5(data).hexdigest()}\n")
                f.write(f"7zip path: {self.sevenzip_path}\n")

            if process_result:
                # Сохраняем вывод 7zip
                output_file = os.path.join(crash_dir, "7zip_output.txt")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write("=== STDOUT ===\n")
                    f.write(process_result.stdout.decode('utf-8', errors='ignore'))
                    f.write("\n=== STDERR ===\n")
                    f.write(process_result.stderr.decode('utf-8', errors='ignore'))
                    f.write(f"\n=== RETURN CODE: {process_result.returncode} ===\n")

            logger.warning(f"CRASH DETECTED! Saved to: {crash_dir}")

        except Exception as e:
            logger.error(f"Error saving crash: {e}")

    def print_stats(self):
        """Выводит статистику фаззинга"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            rate = self.iteration_count / elapsed if elapsed > 0 else 0
            logger.info(f"Progress: {self.iteration_count} iterations | "
                        f"Crashes: {self.crash_count} | "
                        f"Rate: {rate:.1f} iter/sec | "
                        f"Elapsed: {elapsed:.1f}s")

    def fuzz(self, iterations=10000, output_dir="fuzzed_files"):
        """Основной цикл фаззинга"""
        logger.info(f"Starting 7zip fuzzing for {iterations} iterations")
        self.start_time = time.time()

        # Создаем директорию для временных файлов
        os.makedirs(output_dir, exist_ok=True)

        # Загружаем базовый ZIP
        with open(self.base_zip_path, 'rb') as f:
            base_data = f.read()

        logger.info(f"Base ZIP loaded: {len(base_data)} bytes")

        try:
            for i in range(1, iterations + 1):
                self.iteration_count = i

                # Создаем мутированные данные
                mutated_data = self.mutate_zip_structure(base_data)

                # Сохраняем временный файл
                temp_file = os.path.join(output_dir, f"fuzz_{i:06d}.zip")
                with open(temp_file, 'wb') as f:
                    f.write(mutated_data)

                # Тестируем с 7zip
                crash_detected, process_result = self.run_7zip_test(temp_file)

                # Сохраняем сбой если обнаружен
                if crash_detected:
                    self.save_crash(i, mutated_data, process_result)

                # Очищаем временный файл
                try:
                    os.remove(temp_file)
                except:
                    pass

                # Вывод прогресса
                if i % 100 == 0 or crash_detected:
                    self.print_stats()

                # Ранняя остановка если много сбоев
                if self.crash_count >= 50:
                    logger.info("Stopping early due to high crash count")
                    break

        except KeyboardInterrupt:
            logger.info("Fuzzing interrupted by user")
        except Exception as e:
            logger.error(f"Fuzzing error: {e}")
        finally:
            # Финальная статистика
            self.print_stats()
            logger.info(f"Fuzzing completed. Total crashes: {self.crash_count}")


def main():
    parser = argparse.ArgumentParser(
        description='7Zip ZIP Format Fuzzer',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('base_zip', help='Path to base ZIP file for fuzzing')
    parser.add_argument('-i', '--iterations', type=int, default=10000,
                        help='Number of fuzzing iterations (default: 10000)')
    parser.add_argument('-7', '--sevenzip-path', type=str,
                        help='Path to 7z.exe (auto-detected if not specified)')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Enable debug output')
    parser.add_argument('-o', '--output-dir', type=str, default='fuzzed_files',
                        help='Directory for temporary files (default: fuzzed_files)')

    args = parser.parse_args()

    # Настройка логирования
    log_file = setup_logger(args.debug)

    # Создаем необходимые директории
    os.makedirs('crashes', exist_ok=True)

    try:
        # Создаем и запускаем фаззер
        fuzzer = SevenZipFuzzer(
            base_zip_path=args.base_zip,
            sevenzip_path=args.sevenzip_path,
            debug=args.debug
        )

        # Создаем базовый ZIP если нужно
        fuzzer.create_base_zip()

        # Запускаем фаззинг
        fuzzer.fuzz(
            iterations=args.iterations,
            output_dir=args.output_dir
        )

    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        return 1
    finally:
        logger.info(f"Log file: {log_file}")

    return 0


if __name__ == '__main__':
    sys.exit(main())