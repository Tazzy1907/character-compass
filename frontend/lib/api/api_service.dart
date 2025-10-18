import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/card_item.dart';

// A dedicated class for handling API interactions.
class ApiService {
  final bool isTesting = true;

  // --- MOCK DATA FOR TESTING ---
  // This function simulates an API response.
  Future<List<CardItem>> _getMockData() async {
    // Simulate a network delay of 1 second
    await Future.delayed(const Duration(seconds: 1));
    const mockApiResponse = '''
      [
        {"name": "Fantasy", "icon": "fantasy"},
        {"name": "SciFi", "icon": "sciFi"},
        {"name": "Mystery", "icon": "mystery"},
        {"name": "Romance", "icon": "romance"},
        {"name": "Horror", "icon": "horror"},
        {"name": "History", "icon": "history"},
        {"name": "Western", "icon": "western"},
        {"name": "Comics", "icon": "comics"},
        {"name": "Science", "icon": "science"},
        {"name": "Biography", "icon": "biography"},
        {"name": "Business", "icon": "business"},
        {"name": "Cooking", "icon": "cooking"},
        {"name": "Travel", "icon": "travel"},
        {"name": "Music", "icon": "music"},
        {"name": "Art", "icon": "art"},
        {"name": "Poetry", "icon": "poetry"}
      ]
    ''';
    print(mockApiResponse);
    final List<dynamic> jsonResponse = json.decode(mockApiResponse);
    return jsonResponse.map((data) => CardItem.fromJson(data)).toList();
  }

  // --- API FETCH LOGIC ---
  Future<List<CardItem>> fetchCardItems() async {
    if (isTesting) {
      return _getMockData();
    }

    /* // UNCOMMENT THIS BLOCK FOR A REAL API CALL
    const apiUrl = 'https://your-api-domain.com/api/get_books'; 
    try {
      final response = await http.get(Uri.parse(apiUrl));

      if (response.statusCode == 200) {
        final List<dynamic> jsonResponse = json.decode(response.body);
        return jsonResponse.map((data) => CardItem.fromJson(data)).toList();
      } else {
        throw Exception('Failed to load items from API');
      }
    } catch (e) {
      throw Exception('Failed to connect to the API: $e');
    }
    */
    return [];
  }
}
