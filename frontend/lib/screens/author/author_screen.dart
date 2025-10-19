import 'dart:async';
import 'package:flutter/material.dart';
import 'widgets/responsive_icon_grid.dart';
import 'widgets/add_item_dialog.dart';
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
  String? _activelyMonitoredBookId;
  Timer? _activeMonitoringTimer;

  @override
  void initState() {
    super.initState();
    // Fetch the initial list of items when the widget is first created.
    _fetchItems();
  }

  @override
  void dispose() {
    _statusCheckTimer?.cancel();
    _activeMonitoringTimer?.cancel();
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
  void _addItem(BookItem newItem) {
    setState(() {
      _items?.add(newItem);
    });

    // If the new item is processing, start polling
    if (newItem.isProcessing) {
      _startStatusPolling();
    }
  }

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

  // Start active monitoring for a book
  void _startActiveMonitoring(String docId) {
    // Don't start if already monitoring this book
    if (_activelyMonitoredBookId == docId) return;

    // Stop any existing monitoring
    _stopActiveMonitoring();

    // Check if book is processing
    final book = _items?.firstWhere(
      (item) => item.docId == docId,
      orElse: () => _items!.first,
    );

    if (book != null && book.isProcessing) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Cannot monitor while profiles are being generated'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    // Set active monitoring state
    setState(() {
      _activelyMonitoredBookId = docId;

      // Update the book item to show monitoring state
      if (_items != null) {
        for (int i = 0; i < _items!.length; i++) {
          if (_items![i].docId == docId) {
            _items![i] = _items![i].copyWith(isActivelyMonitored: true);
          } else {
            // Ensure other books are not marked as monitored
            _items![i] = _items![i].copyWith(isActivelyMonitored: false);
          }
        }
      }
    });

    // Start polling every 60 seconds
    print('⏰ Starting monitoring timer for $docId - checks every 60 seconds');
    _activeMonitoringTimer = Timer.periodic(const Duration(seconds: 60), (_) {
      print('⏰ Timer fired - checking for changes');
      _checkActiveBookForChanges();
    });

    // Also do an immediate check
    print('🔄 Performing immediate initial check');
    _checkActiveBookForChanges();

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Now monitoring ${book?.name ?? 'book'} for changes'),
        backgroundColor: Colors.green,
      ),
    );
  }

  // Stop active monitoring
  void _stopActiveMonitoring() {
    if (_activelyMonitoredBookId == null) return;

    _activeMonitoringTimer?.cancel();

    setState(() {
      // Update the book item to remove monitoring state
      if (_items != null) {
        for (int i = 0; i < _items!.length; i++) {
          if (_items![i].docId == _activelyMonitoredBookId) {
            _items![i] = _items![i].copyWith(isActivelyMonitored: false);
            break;
          }
        }
      }
      _activelyMonitoredBookId = null;
    });
  }

  // Check actively monitored book for changes
  Future<void> _checkActiveBookForChanges() async {
    if (_activelyMonitoredBookId == null) return;

    print('📊 Checking book for changes: $_activelyMonitoredBookId');

    try {
      final result = await _apiService.checkDocumentChanges(
        _activelyMonitoredBookId!,
      );

      print('📊 Check result: $result');

      if (!mounted) return;

      final error = result['error'];

      // Handle errors
      if (error != null) {
        // Only stop monitoring for serious errors (generation in progress for THIS book)
        // Backend will now auto-switch to the monitored book if needed
        if (error.toString().contains('generation is running')) {
          _stopActiveMonitoring();

          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Monitoring stopped: Profile generation started'),
              backgroundColor: Colors.orange,
            ),
          );
        } else {
          // For other errors, just log them and continue monitoring
          // (will retry on next interval)
          print('Error checking document (continuing monitoring): $error');
        }
        return;
      }

      // Check if changes were detected
      final changed = result['changed'] ?? false;

      if (changed) {
        final charactersUpdated =
            result['characters_updated'] as List<String>? ?? [];
        final chunksAdded = result['chunks_added'] ?? 0;
        final chunksDeleted = result['chunks_deleted'] ?? 0;

        // Show notification about changes
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Document updated! '
              '${charactersUpdated.length} characters refreshed. '
              '($chunksAdded added, $chunksDeleted removed chunks)',
            ),
            backgroundColor: Colors.blue,
            duration: const Duration(seconds: 5),
            action: SnackBarAction(
              label: 'View',
              textColor: Colors.white,
              onPressed: () {
                // Could navigate to the book screen here
              },
            ),
          ),
        );

        // Refresh book list to get updated data
        _fetchItems();
      }
    } catch (e) {
      print('Error checking active book for changes: $e');
      // Don't show error to user, will retry on next interval
    }
  }

  // Toggle active monitoring for a book
  void _toggleActiveMonitoring(String docId) {
    if (_activelyMonitoredBookId == docId) {
      _stopActiveMonitoring();
    } else {
      _startActiveMonitoring(docId);
    }
  }

  // Shows the dialog and waits for the user to submit a new item.
  void _showAddItemDialog() async {
    final newItem = await showDialog<BookItem>(
      context: context,
      builder: (BuildContext context) {
        return const AddItemDialog();
      },
    );

    // If the user created a new item, add it to the list.
    if (newItem != null) {
      _addItem(newItem);
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
      onToggleMonitoring: _toggleActiveMonitoring,
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
      ),
      body: _buildBody(),
      floatingActionButton: FloatingActionButton(
        onPressed: _showAddItemDialog, // This now calls our dialog function
        backgroundColor: highlightColor,
        elevation: 10.0,
        child: const Icon(Icons.add, color: Colors.white),
      ),
    );
  }
}
