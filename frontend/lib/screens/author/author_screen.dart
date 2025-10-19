import 'package:flutter/material.dart';
import 'widgets/responsive_icon_grid.dart';
import 'widgets/add_item_dialog.dart';
import '../../models/card_item.dart';
import '../../api/api_service.dart';
import '../../style.dart';

// HomeScreen is now a StatefulWidget to manage the list of items.
class AuthorScreen extends StatefulWidget {
  const AuthorScreen({super.key});

  @override
  State<AuthorScreen> createState() => _AuthorscreenState();
}

class _AuthorscreenState extends State<AuthorScreen> {
  final ApiService _apiService = ApiService();
  List<CardItem>? _items;
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
      final items = await _apiService.fetchCardItems();
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

  // Adds a new item to the list and rebuilds the UI.
  void _addItem(CardItem newItem) {
    setState(() {
      _items?.add(newItem);
    });
  }

  // Shows the dialog and waits for the user to submit a new item.
  void _showAddItemDialog() async {
    final newItem = await showDialog<CardItem>(
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
    return ResponsiveIconGrid(items: _items!);
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
      floatingActionButton: FloatingActionButton(
        onPressed: _showAddItemDialog, // This now calls our dialog function
        backgroundColor: highlightColor,
        elevation: 10.0,
        child: const Icon(Icons.add, color: Colors.white),
      ),
    );
  }
}
