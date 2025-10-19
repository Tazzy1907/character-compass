import 'package:flutter/material.dart';
import '../../api/api_service.dart';
import '../../models/character_details.dart';
import '../../style.dart';

class CharacterScreen extends StatefulWidget {
  final int characterId;

  const CharacterScreen({super.key, required this.characterId});

  @override
  State<CharacterScreen> createState() => _CharacterScreenState();
}

class _CharacterScreenState extends State<CharacterScreen>
    with SingleTickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  CharacterDetails? _character;
  String? _error;
  bool _isLoading = true;
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _fetchCharacter();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _fetchCharacter() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final character = await _apiService.fetchCharacterById(
        widget.characterId,
      );
      setState(() {
        _character = character;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  void _showChatPlaceholder() {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          'Chat with ${_character?.name ?? "character"} (Coming soon!)',
        ),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F7F8),
      appBar: AppBar(
        backgroundColor: darkColor,
        iconTheme: const IconThemeData(color: Colors.white),
        title: Text(
          _character?.name ?? "CharacterDetails Profile",
          style: const TextStyle(color: Colors.white),
        ),
        bottom: _character != null
            ? TabBar(
                controller: _tabController,
                indicatorColor: highlightColor,
                labelColor: Colors.white,
                unselectedLabelColor: Colors.white70,
                tabs: const [
                  Tab(icon: Icon(Icons.person), text: "Overview"),
                  Tab(icon: Icon(Icons.history_edu), text: "Backstory"),
                  Tab(icon: Icon(Icons.people), text: "Relationships"),
                  Tab(icon: Icon(Icons.flag), text: "Goals"),
                ],
              )
            : null,
      ),
      body: _buildBody(),
      floatingActionButton: _character != null
          ? FloatingActionButton.extended(
              onPressed: _showChatPlaceholder,
              backgroundColor: highlightColor,
              icon: const Icon(Icons.chat_bubble, color: Colors.white),
              label: const Text("Chat", style: TextStyle(color: Colors.white)),
            )
          : null,
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 64, color: Colors.red),
              const SizedBox(height: 16),
              Text(
                'Error loading character',
                style: TextStyle(fontSize: 18, color: Colors.grey[700]),
              ),
              const SizedBox(height: 8),
              Text(
                _error!,
                style: TextStyle(fontSize: 14, color: Colors.grey[500]),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: _fetchCharacter,
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: highlightColor,
                  foregroundColor: Colors.white,
                ),
              ),
            ],
          ),
        ),
      );
    }

    if (_character == null) {
      return const Center(child: Text('No character data'));
    }

    return TabBarView(
      controller: _tabController,
      children: [
        _buildOverviewTab(),
        _buildBackstoryTab(),
        _buildRelationshipsTab(),
        _buildGoalsTab(),
      ],
    );
  }

  Widget _buildOverviewTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // CharacterDetails Header Card
          Card(
            elevation: 4,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  CircleAvatar(
                    backgroundColor: _character!.characterType == 'main'
                        ? highlightColor
                        : lightColor,
                    radius: 50,
                    child: Text(
                      _character!.name[0].toUpperCase(),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 40,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    _character!.name,
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  if (_character!.briefDescription.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(
                      _character!.briefDescription,
                      style: TextStyle(fontSize: 16, color: Colors.grey[600]),
                    ),
                  ],
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: _character!.characterType == 'main'
                          ? highlightColor.withOpacity(0.2)
                          : lightColor.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      _character!.characterType.toUpperCase(),
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: _character!.characterType == 'main'
                            ? highlightColor
                            : lightColor,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Basic Info Card
          _buildInfoCard('Basic Information', Icons.info_outline, [
            if (_character!.age != null)
              _buildInfoRow('Age', '${_character!.age}'),
            if (_character!.gender != null)
              _buildInfoRow('Gender', _character!.gender!),
            if (_character!.sex != null) _buildInfoRow('Sex', _character!.sex!),
            if (_character!.race != null)
              _buildInfoRow('Race', _character!.race!),
            if (_character!.occupation != null &&
                _character!.occupation!.isNotEmpty)
              _buildInfoRow('Occupation', _character!.occupation!),
          ]),

          // Personality Card
          if (_character!.hasPersonality) ...[
            const SizedBox(height: 16),
            _buildSectionCard(
              'Personality',
              Icons.psychology,
              _character!.personality!,
            ),
          ],

          // Appearance Card
          if (_character!.hasAppearance) ...[
            const SizedBox(height: 16),
            _buildSectionCard(
              'Appearance',
              Icons.face,
              _character!.appearance!,
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildBackstoryTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: _character!.hasBackstory
          ? _buildSectionCard(
              'Backstory',
              Icons.history_edu,
              _character!.backstory!,
            )
          : Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.history_edu, size: 64, color: Colors.grey[400]),
                  const SizedBox(height: 16),
                  Text(
                    'No backstory available',
                    style: TextStyle(fontSize: 16, color: Colors.grey[600]),
                  ),
                ],
              ),
            ),
    );
  }

  Widget _buildRelationshipsTab() {
    return _character!.hasRelationships
        ? ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: _character!.relationships.length,
            itemBuilder: (context, index) {
              return Card(
                elevation: 2,
                margin: const EdgeInsets.only(bottom: 12),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                child: ListTile(
                  leading: CircleAvatar(
                    backgroundColor: lightColor,
                    child: const Icon(Icons.person, color: Colors.white),
                  ),
                  title: Text(
                    _character!.relationships[index],
                    style: const TextStyle(fontSize: 16),
                  ),
                ),
              );
            },
          )
        : Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.people_outline, size: 64, color: Colors.grey[400]),
                const SizedBox(height: 16),
                Text(
                  'No relationships recorded',
                  style: TextStyle(fontSize: 16, color: Colors.grey[600]),
                ),
              ],
            ),
          );
  }

  Widget _buildGoalsTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Goals Section
          _buildListSection(
            'Goals',
            Icons.flag,
            _character!.goals,
            highlightColor,
          ),
          const SizedBox(height: 24),
          // Motivations Section
          _buildListSection(
            'Motivations',
            Icons.psychology,
            _character!.motivations,
            lightColor,
          ),
        ],
      ),
    );
  }

  Widget _buildInfoCard(String title, IconData icon, List<Widget> children) {
    if (children.isEmpty) {
      return const SizedBox.shrink();
    }

    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: darkColor, size: 24),
                const SizedBox(width: 12),
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: darkColor,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ...children,
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              '$label:',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: Colors.grey[700],
              ),
            ),
          ),
          Expanded(child: Text(value, style: const TextStyle(fontSize: 14))),
        ],
      ),
    );
  }

  Widget _buildSectionCard(String title, IconData icon, String content) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: darkColor, size: 24),
                const SizedBox(width: 12),
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: darkColor,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text(content, style: const TextStyle(fontSize: 15, height: 1.5)),
          ],
        ),
      ),
    );
  }

  Widget _buildListSection(
    String title,
    IconData icon,
    List<String> items,
    Color color,
  ) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 24),
                const SizedBox(width: 12),
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            if (items.isEmpty)
              Text(
                'No $title recorded',
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.grey[600],
                  fontStyle: FontStyle.italic,
                ),
              )
            else
              ...items.asMap().entries.map((entry) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        margin: const EdgeInsets.only(top: 6),
                        width: 8,
                        height: 8,
                        decoration: BoxDecoration(
                          color: color,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          entry.value,
                          style: const TextStyle(fontSize: 15),
                        ),
                      ),
                    ],
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }
}
