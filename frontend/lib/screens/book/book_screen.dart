import 'package:flutter/material.dart';
import '../../api/api_service.dart';
import '../../models/character_item.dart';
import '../../style.dart';
import './widgets/responsive_character_grid.dart';

class BookScreen extends StatefulWidget {
  final String bookId;
  const BookScreen({super.key, required this.bookId});

  @override
  State<BookScreen> createState() => _MyWidgetState();
}

class _MyWidgetState extends State<BookScreen> {
  final ApiService _apiService = ApiService();
  List<CharacterItem>? _items;
  String? _error;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    // Fetch the initial list of items when the widget is first created.
    _fetchItems();
  }

  Future<void> _fetchItems() async {
    try {
      final items = await _apiService.fetchCharacterItems(widget.bookId);
      setState(() {
        _items = items;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
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
    return ResponsiveCharacterGrid(items: _items!);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: darkColor,
        title: const Text(
          "CharacterCompass",
          style: TextStyle(color: Colors.white),
        ),
      ),
      body: _buildBody(),
      // floatingActionButton: FloatingActionButton(
      //   onPressed: _showAddItemDialog, // This now calls our dialog function
      //   backgroundColor: highlightColor,
      //   elevation: 10.0,
      //   child: const Icon(Icons.add, color: Colors.white),
      // ),
    );
  }
}
