import 'package:flutter/material.dart';
import 'tasks_screen.dart';
import 'shopping_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text('Домашние дела'),
          bottom: TabBar(
            tabs: [
              Tab(text: '📋 Задачи', icon: Icon(Icons.task)),
              Tab(text: '🛒 Покупки', icon: Icon(Icons.shopping_cart)),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            TasksScreen(),
            ShoppingScreen(),
          ],
        ),
      ),
    );
  }
}