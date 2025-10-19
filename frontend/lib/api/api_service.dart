import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/book_item.dart';
import '../models/character_item.dart';
import '../models/character_details.dart';

// A dedicated class for handling API interactions.
class ApiService {
  final bool isTesting = false;
  final String baseUrl = "http://localhost:8000";

  // --- MOCK DATA FOR TESTING ---
  // This function simulates an API response.
  Future<List<BookItem>> _getMockData() async {
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
    return jsonResponse.map((data) => BookItem.fromJson(data)).toList();
  }

  // --- API FETCH LOGIC ---
  Future<List<BookItem>> fetchCardItems() async {
    if (isTesting) {
      return _getMockData();
    }

    final apiUrl = "$baseUrl/api/books";
    try {
      final response = await http.get(Uri.parse(apiUrl));

      if (response.statusCode == 200) {
        final List<dynamic> jsonResponse = json.decode(response.body);
        return jsonResponse.map((data) => BookItem.fromJson(data)).toList();
      } else {
        throw Exception('Failed to load items from API');
      }
    } catch (e) {
      throw Exception('Failed to connect to the API: $e');
    }
  }

  Future<List<CharacterItem>> fetchCharacterItems(String docId) async {
    final apiUrl = "$baseUrl/api/books/$docId/characters";
    try {
      final response = await http.get(Uri.parse(apiUrl));

      if (response.statusCode == 200) {
        final Map<String, dynamic> jsonResponse = json.decode(response.body);
        print(jsonResponse);
        final List<dynamic> charactersJson =
            jsonResponse['characters'] as List<dynamic>;
        return charactersJson
            .map((data) => CharacterItem.fromJson(data as Map<String, dynamic>))
            .toList();
      } else {
        throw Exception('Failed to load items from API');
      }
    } catch (e) {
      throw Exception('Failed to connect to the API: $e');
    }
  }

  Future<CharacterDetails> fetchCharacterDetails(int characterId) async {
    final apiUrl = "$baseUrl/api/characters/$characterId";
    try {
      final response = await http.get(Uri.parse(apiUrl));

      if (response.statusCode == 200) {
        final dynamic jsonResponse = json.decode(response.body);
        return CharacterDetails.fromJson(jsonResponse);
      } else {
        throw Exception('Failed to load items from API');
      }
    } catch (e) {
      throw Exception('Failed to connect to the API: $e');
    }
  }

  // --- CHARACTER API METHODS ---

  /// Fetch a specific character by ID
  Future<CharacterDetails> fetchCharacterById(int characterId) async {
    if (isTesting) {
      // Return mock character for testing
      await Future.delayed(const Duration(seconds: 1));
      return CharacterDetails(
        id: characterId,
        name: "Sample Character",
        bookUrl: "test_book_1",
        characterType: "main",
        age: 25,
        gender: "Female",
        sex: "Female",
        race: "Human",
        occupation: "Detective",
        personality:
            "Brave, intelligent, and determined. Has a strong sense of justice and never gives up on a case.",
        appearance:
            "Tall with dark hair and piercing blue eyes. Usually wears a long coat.",
        backstory:
            "A skilled detective who joined the force after her mentor was killed in the line of duty. She has dedicated her life to solving cold cases.",
        relationships: [
          "Partner with John Smith",
          "Friend of Sarah Johnson",
          "Mentored by Captain Williams",
        ],
        goals: ["Solve the cold case", "Find the truth", "Bring justice"],
        motivations: ["Justice", "Honor her mentor's memory", "Protect others"],
      );
    }

    try {
      final url = Uri.parse('$baseUrl/api/characters/$characterId');
      final response = await http.get(url);

      if (response.statusCode == 200) {
        final jsonResponse = json.decode(response.body);
        return CharacterDetails.fromJson(jsonResponse);
      } else if (response.statusCode == 404) {
        throw Exception('Character not found');
      } else {
        throw Exception('Failed to load character: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to fetch character: $e');
    }
  }

  // --- BOOK SCAN API METHODS ---

  /// Scan the stories folder for new txt files
  Future<Map<String, dynamic>> scanStoriesFolder() async {
    final apiUrl = "$baseUrl/api/books/scan";
    try {
      final response = await http.get(Uri.parse(apiUrl));

      if (response.statusCode == 200) {
        final jsonResponse = json.decode(response.body);
        return {
          'success': jsonResponse['success'] ?? false,
          'found': jsonResponse['found'] ?? 0,
          'new_books': jsonResponse['new_books'] ?? [],
          'message': jsonResponse['message'] ?? '',
        };
      } else {
        throw Exception(
          'Failed to scan stories folder: ${response.statusCode}',
        );
      }
    } catch (e) {
      throw Exception('Failed to scan stories folder: $e');
    }
  }

  /// Check the status of profile generation
  Future<Map<String, dynamic>> checkGenerationStatus() async {
    final apiUrl = "$baseUrl/api/generate/status";
    try {
      final response = await http.get(Uri.parse(apiUrl));

      if (response.statusCode == 200) {
        final jsonResponse = json.decode(response.body);
        return {
          'is_running': jsonResponse['is_running'] ?? false,
          'book_url': jsonResponse['book_url'],
          'started_at': jsonResponse['started_at'],
          'message': jsonResponse['message'] ?? '',
          'error': jsonResponse['error'],
        };
      } else {
        throw Exception(
          'Failed to check generation status: ${response.statusCode}',
        );
      }
    } catch (e) {
      throw Exception('Failed to check generation status: $e');
    }
  }

  // --- ACTIVE MONITORING API METHODS ---

  /// Check a document for changes and update character profiles
  Future<Map<String, dynamic>> checkDocumentChanges(String docId) async {
    final apiUrl = "$baseUrl/api/books/$docId/check-changes";
    try {
      final response = await http.post(
        Uri.parse(apiUrl),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({}), // Empty body for POST request
      );

      if (response.statusCode == 200) {
        final jsonResponse = json.decode(response.body);
        return {
          'changed': jsonResponse['changed'] ?? false,
          'chunks_added': jsonResponse['chunks_added'] ?? 0,
          'chunks_deleted': jsonResponse['chunks_deleted'] ?? 0,
          'characters_updated': List<String>.from(
            jsonResponse['characters_updated'] ?? [],
          ),
          'last_modified': jsonResponse['last_modified'] ?? '',
          'message': jsonResponse['message'] ?? '',
          'error': jsonResponse['error'],
        };
      } else {
        throw Exception(
          'Failed to check document changes: ${response.statusCode}',
        );
      }
    } catch (e) {
      throw Exception('Failed to check document changes: $e');
    }
  }
}
