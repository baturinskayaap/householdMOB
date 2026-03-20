import 'package:shared_preferences/shared_preferences.dart';

class AppConfig {
  static String baseUrl = 'http://192.168.1.100:8000'; // значение по умолчанию

  static Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    final savedIp = prefs.getString('server_ip');
    if (savedIp != null && savedIp.isNotEmpty) {
      baseUrl = savedIp;
    } else {
      // Если нет сохранённого, можно оставить дефолтный или записать его
      await prefs.setString('server_ip', baseUrl);
    }
  }

  static Future<void> save(String newIp) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('server_ip', newIp);
    baseUrl = newIp;
  }
}