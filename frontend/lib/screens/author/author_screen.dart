import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'widgets/responsive_icon_grid.dart';
import '../../models/book_item.dart';
import '../../api/api_service.dart';
import '../../style.dart';

// AuthorScreen is now a StatefulWidget to manage the list of items.
class AuthorScreen extends StatefulWidget {
  const AuthorScreen({super.key});

  @override
  State<AuthorScreen> createState() => _AuthorScreenState();
}

class _AuthorScreenState extends State<AuthorScreen> {
  final ApiService _apiService = ApiService();
  List<BookItem>? _items;
  String? _error;
  bool _isLoading = true;
  Timer? _statusCheckTimer;

  @override
  void initState() {
    super.initState();
    // Fetch the initial list of items when the widget is first created.
    _fetchItems();
  }

  @override
  void dispose() {
    _statusCheckTimer?.cancel();
    super.dispose();
  }

  Future<void> _fetchItems() async {
    try {
      final items = await _apiService.fetchCardItems();
      setState(() {
        _items = items;
        _isLoading = false;
      });

      // After fetching items, check if there's any ongoing generation
      // and sync the UI state with backend
      await _syncProcessingState();
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  /// Sync the processing state with backend on page load
  Future<void> _syncProcessingState() async {
    try {
      final status = await _apiService.checkGenerationStatus();
      final isRunning = status['is_running'] ?? false;
      final bookUrl = status['book_url'];
      final error = status['error'];

      if (_items == null || bookUrl == null) return;

      if (isRunning) {
        // There's an active generation - mark the book as processing
        setState(() {
          for (int i = 0; i < _items!.length; i++) {
            if (_items![i].docId == bookUrl) {
              _items![i] = _items![i].copyWith(isProcessing: true);
              break;
            }
          }
        });

        // Start polling since there's active generation
        _startStatusPolling();
      } else if (error != null) {
        // Generation recently failed - mark the book with error
        setState(() {
          for (int i = 0; i < _items!.length; i++) {
            if (_items![i].docId == bookUrl) {
              _items![i] = _items![i].copyWith(
                isProcessing: false,
                error: error,
              );
              break;
            }
          }
        });
      }
    } catch (e) {
      print('Error syncing processing state: $e');
    }
  }

  // Adds a new item to the list and rebuilds the UI.
  // Start polling for generation status
  void _startStatusPolling() {
    // Cancel existing timer if any
    _statusCheckTimer?.cancel();

    // Create a new periodic timer that checks every 5 seconds
    _statusCheckTimer = Timer.periodic(const Duration(seconds: 5), (timer) {
      _checkGenerationStatus();
    });
  }

  // Check the generation status and update UI accordingly
  Future<void> _checkGenerationStatus() async {
    try {
      final status = await _apiService.checkGenerationStatus();

      if (!mounted) return;

      final isRunning = status['is_running'] ?? false;
      final bookUrl = status['book_url'];
      final error = status['error'];

      if (!isRunning && _items != null && bookUrl != null) {
        // Generation finished - update the processing book
        bool hasProcessingItems = false;

        setState(() {
          for (int i = 0; i < _items!.length; i++) {
            if (_items![i].isProcessing && _items![i].docId == bookUrl) {
              // This book just finished processing
              if (error != null) {
                // Generation failed
                _items![i] = _items![i].copyWith(
                  isProcessing: false,
                  error: error,
                );

                // Show error message to user
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(
                      'Failed to generate profiles for ${_items![i].name}: $error',
                    ),
                    backgroundColor: Colors.red,
                    duration: const Duration(seconds: 5),
                  ),
                );
              } else {
                // Generation succeeded
                _items![i] = _items![i].copyWith(isProcessing: false);

                // Show success message
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(
                      'Successfully generated profiles for ${_items![i].name}',
                    ),
                    backgroundColor: Colors.green,
                    duration: const Duration(seconds: 3),
                  ),
                );
              }
            } else if (_items![i].isProcessing) {
              // Still has processing items
              hasProcessingItems = true;
            }
          }
        });

        // If no more processing items, stop polling
        if (!hasProcessingItems) {
          _statusCheckTimer?.cancel();
        }

        // Refresh the list from the server to get updated data (only if no error)
        if (error == null) {
          _fetchItems();
        }
      }
    } catch (e) {
      // Silently fail - we'll try again on next poll
      print('Error checking generation status: $e');
    }
  }

  // Check a specific book for changes
  Future<void> _checkBookForChanges(String filePath) async {
    try {
      final result = await _apiService.checkDocumentChanges(filePath);

      if (!mounted) return;

      final error = result['error'];

      // Handle errors
      if (error != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $error'), backgroundColor: Colors.red),
        );
        return;
      }

      // Check if changes were detected
      final changed = result['changed'] ?? false;

      if (changed) {
        final charactersUpdated =
            result['characters_updated'] as List<String>? ?? [];
        final charactersRemoved =
            result['characters_removed'] as List<String>? ?? [];
        final chunksAdded = result['chunks_added'] ?? 0;
        final chunksDeleted = result['chunks_deleted'] ?? 0;

        // Build message with character changes
        String message = 'Changes detected! ';
        if (charactersUpdated.isNotEmpty) {
          message += '${charactersUpdated.length} characters updated. ';
        }
        if (charactersRemoved.isNotEmpty) {
          message += '${charactersRemoved.length} characters removed. ';
        }
        message += '($chunksAdded added, $chunksDeleted deleted chunks)';

        // Refresh book list to get updated data
        await _fetchItems();

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(message),
            backgroundColor: Colors.blue,
            duration: const Duration(seconds: 5),
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('No changes detected'),
            duration: Duration(seconds: 2),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  // Shows the dialog and waits for the user to submit a new item.
  // Generate character profiles for a book
  Future<void> _generateProfiles(String filePath) async {
    try {
      // Call generate API
      final response = await http.post(
        Uri.parse('${_apiService.baseUrl}/api/generate'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'book_url': filePath,
          'book_name': null,
          'book_icon': null,
        }),
      );

      if (!mounted) return;

      if (response.statusCode == 200) {
        final result = json.decode(response.body);
        if (result['success'] == true) {
          // Mark book as processing
          setState(() {
            final bookIndex = _items?.indexWhere(
              (item) => item.docId == filePath,
            );
            if (bookIndex != null && bookIndex >= 0) {
              _items![bookIndex] = _items![bookIndex].copyWith(
                isProcessing: true,
              );
            }
          });

          // Start polling for status
          _startStatusPolling();

          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                'Profile generation started for ${result['book_url']}',
              ),
              backgroundColor: Colors.green,
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(result['message'] ?? 'Generation failed'),
              backgroundColor: Colors.orange,
            ),
          );
        }
      } else {
        throw Exception('HTTP ${response.statusCode}');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error starting generation: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  // Scan stories folder for new txt files
  Future<void> _scanAndRefresh() async {
    try {
      // Call scan API
      final result = await _apiService.scanStoriesFolder();

      // Refresh book list
      await _fetchItems();

      // Show result
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result['message'] ?? 'Scan complete'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Scan failed: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  // Helper method to decide which widget to show based on the current state.
  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return Center(child: Text('Error: $_error'));
    }
    if (_items == null || _items!.isEmpty) {
      return const Center(child: Text('No items found.'));
    }
    // If data is loaded successfully, show the grid.
    return ResponsiveIconGrid(
      items: _items!,
      onCheckChanges: _checkBookForChanges,
      onGenerate: _generateProfiles,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: darkColor,
        centerTitle: true,
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Image.asset(
              'icons/Character Compass Icon.jpeg',
              height: 32,
              fit: BoxFit.contain,
            ),
            const SizedBox(width: 12),
            const Text(
              "CharacterCompass",
              style: TextStyle(color: Colors.white),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Scan for new stories',
            onPressed: _scanAndRefresh,
          ),
        ],
      ),
      body: _buildBody(),
    );
  }
}
